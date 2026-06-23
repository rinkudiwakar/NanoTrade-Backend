#include "utils/affinity.h"

#if defined(_WIN32)
#include <windows.h>
void set_thread_affinity(int cpu) {
  DWORD_PTR mask = ((DWORD_PTR)1) << cpu;
  SetThreadAffinityMask(GetCurrentThread(), mask);
}
#else
#include <pthread.h>
#include <sched.h>
void set_thread_affinity(int cpu) {
  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  CPU_SET(cpu, &cpuset);
  pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
}
#endif
