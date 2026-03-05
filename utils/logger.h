#pragma once
#include <string>

namespace Logger
{
    void info(const std::string& message);
    void warn(const std::string& message);
    void error(const std::string& message);
}
