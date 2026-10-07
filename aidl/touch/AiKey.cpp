/*
 * SPDX-License-Identifier: Apache-2.0
 */

#define LOG_TAG "vendor.lineage.touch-service.xiaomi"

#include "AiKey.h"

#include <android-base/logging.h>

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <unistd.h>

#include <cstring>
#include <string>
#include <vector>

namespace aidl::vendor::lineage::touch {

namespace {

constexpr int kAiKeyCode = 689;
constexpr char kInputDir[] = "/dev/input";

bool hasKeyCode(int fd, int code) {
    constexpr int kBits = KEY_MAX + 1;

    unsigned long bits[
        (kBits + (sizeof(unsigned long) * 8 - 1)) /
        (sizeof(unsigned long) * 8)
    ]{};

    if (ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(bits)), bits) < 0) {
        return false;
    }

    return (bits[code / (sizeof(unsigned long) * 8)] &
            (1UL << (code % (sizeof(unsigned long) * 8)))) != 0;
}

std::vector<int> findDevices() {
    std::vector<int> devices;
    DIR* dir = opendir(kInputDir);
    if (!dir) {
        PLOG(ERROR) << "Failed to open " << kInputDir;
        return devices;
    }

    dirent* entry;
    while ((entry = readdir(dir)) != nullptr) {
        if (strncmp(entry->d_name, "event", 5) != 0) {
            continue;
        }

        const std::string path = std::string(kInputDir) + "/" + entry->d_name;
        const int fd = open(path.c_str(), O_RDONLY | O_NONBLOCK | O_CLOEXEC);
        if (fd < 0) {
            continue;
        }

        if (hasKeyCode(fd, kAiKeyCode)) {
            char name[256]{};
            ioctl(fd, EVIOCGNAME(sizeof(name)), name);
            LOG(INFO) << "AI key input device: " << path << " (" << name << ")";
            devices.push_back(fd);
        } else {
            close(fd);
        }
    }

    closedir(dir);
    return devices;
}

} // namespace

AiKey::~AiKey() {
    stop();
}

void AiKey::start() {
    if (mThread.joinable()) {
        return;
    }

    mRunning = true;
    mThread = std::thread(&AiKey::monitor, this);
}

void AiKey::stop() {
    mRunning = false;
    if (mThread.joinable()) {
        mThread.join();
    }
}

void AiKey::monitor() {
    LOG(INFO) << "AI key monitor started (Linux key code " << kAiKeyCode << ")";

    while (mRunning) {
        auto devices = findDevices();

        if (devices.empty()) {
            usleep(1000 * 1000);
            continue;
        }

        std::vector<pollfd> fds;
        fds.reserve(devices.size());

        for (const int fd : devices) {
            fds.push_back({.fd = fd, .events = POLLIN, .revents = 0});
        }

        while (mRunning) {
            const int ret = poll(fds.data(), fds.size(), 1000);

            if (ret < 0) {
                if (errno == EINTR) {
                    continue;
                }

                PLOG(ERROR) << "Failed polling AI key input device";
                break;
            }

            if (ret == 0) {
                continue;
            }

            for (auto& pfd : fds) {
                if (!(pfd.revents & POLLIN)) {
                    continue;
                }

                input_event event{};

                while (read(pfd.fd, &event, sizeof(event)) == sizeof(event)) {
                    if (event.type != EV_KEY || event.code != kAiKeyCode) {
                        continue;
                    }

                    switch (event.value) {
                        case 1:
                            LOG(INFO) << "AI key pressed";
                            break;
                        case 0:
                            LOG(INFO) << "AI key released";
                            break;
                        case 2:
                            LOG(INFO) << "AI key repeat";
                            break;
                        default:
                            break;
                    }
                }
            }
        }

        for (const int fd : devices) {
            close(fd);
        }
    }

    LOG(INFO) << "AI key monitor stopped";
}

} // namespace aidl::vendor::lineage::touch
