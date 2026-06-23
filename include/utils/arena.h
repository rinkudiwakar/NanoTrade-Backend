#pragma once
#include <cstddef>
#include <vector>

class SimpleArena {
public:
  explicit SimpleArena(size_t blockSize = 1 << 20) : blockSize(blockSize) {}
  ~SimpleArena() { clear(); }

  void *allocate(size_t sz) {
    if (sz > blockSize)
      return ::operator new(sz);
    if (current + sz > blockSize) {
      blocks.emplace_back(new char[blockSize]);
      current = 0;
    }
    void *ptr = blocks.back().get() + current;
    current += sz;
    return ptr;
  }

  void reset() {
    blocks.clear();
    current = blockSize; // force new allocation on next allocate
  }

  void clear() {
    blocks.clear();
    current = blockSize;
  }

private:
  size_t blockSize;
  size_t current = 0;
  std::vector<std::unique_ptr<char[]>> blocks;
};
