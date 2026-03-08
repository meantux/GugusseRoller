cmake_minimum_required(VERSION 3.16)
project(GugusseCamera CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Optimise for the Pi 4B's Cortex-A72
add_compile_options(-O2 -march=armv8-a+crc -mtune=cortex-a72)

find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBCAMERA REQUIRED libcamera)
pkg_check_modules(LIBTIFF   REQUIRED libtiff-4)

add_executable(camera_test
    GCamera.cpp
    DngWriter.cpp
    main_test.cpp
)

target_include_directories(camera_test PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${LIBCAMERA_INCLUDE_DIRS}
    ${LIBTIFF_INCLUDE_DIRS}
)

target_link_libraries(camera_test PRIVATE
    ${LIBCAMERA_LIBRARIES}
    ${LIBTIFF_LIBRARIES}
)

target_compile_definitions(camera_test PRIVATE
    ${LIBCAMERA_CFLAGS_OTHER}
)
