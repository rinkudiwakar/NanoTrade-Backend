FROM python:3.13-slim AS builder

# Install build dependencies for C++ and pybind11
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy C++ source and build configurations
COPY CMakeLists.txt .
COPY src/ src/
COPY include/ include/

# Build the C++ extension
RUN mkdir build && cd build && \
    cmake -DPRODUCTION_BUILD=ON .. && \
    make _nanotrade_ext -j$(nproc)

# ---------------------------------------------------
# RUNTIME STAGE
# ---------------------------------------------------
FROM python:3.13-slim

# Set working directory to /app
WORKDIR /app

# Copy the built C++ extension
COPY --from=builder /app/build/_nanotrade_ext*.so /app/build/

# Copy requirements and install
COPY python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Assuming local structure has the python folder
COPY python/ /app/python/

# Ensure Python can find the built extension and the app package
ENV PYTHONPATH=/app/build:/app/python

# Expose API port
EXPOSE 8000

# We use an entrypoint script or direct command in docker-compose
# By default, start the API if run without args
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
