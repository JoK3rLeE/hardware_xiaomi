/*
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <atomic>
#include <thread>

namespace aidl::vendor::lineage::touch {

class AiKey {
  public:
    ~AiKey();

    void start();
    void stop();

  private:
    void monitor();

    std::atomic<bool> mRunning{false};
    std::thread mThread;
};

} // namespace aidl::vendor::lineage::touch
