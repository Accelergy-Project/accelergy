cmake_minimum_required(VERSION 3.14)
project(sim)

set(CMAKE_CXX_STANDARD 14)

add_executable(sim main.cpp accelergy.cpp accelergyComponent.cpp PE.cpp mac.cpp memory.cpp memory.h)

include_directories(include)

find_library(LIB_PATH yaml-cpp)
target_link_libraries(sim "${LIB_PATH}")
