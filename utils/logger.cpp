#include "logger.h"
#include <iostream>
#include <chrono>
#include <ctime>

std::string currentTime()
{
    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);
    return std::ctime(&time);
}

void Logger::info(const std::string& message)
{
    std::cout << "[INFO] " << message << std::endl;
}

void Logger::warn(const std::string& message)
{
    std::cout << "[WARN] " << message << std::endl;
}

void Logger::error(const std::string& message)
{
    std::cout << "[ERROR] " << message << std::endl;
}
