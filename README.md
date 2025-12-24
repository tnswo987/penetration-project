# Intelligent Robotic Sorting System with PdM
![OS](https://img.shields.io/badge/OS-Ubuntu%2022.04-E95420)
![OS](https://img.shields.io/badge/OS-Windows%2011-blue)

![Language](https://img.shields.io/badge/Language-C-lightgrey)
![Language](https://img.shields.io/badge/Language-Python%203.8%2B-3776AB)

![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![Robotics](https://img.shields.io/badge/Robotics-SLAM-green)
![Robotics](https://img.shields.io/badge/Robotics-Hand--Eye%20Calibration-orange)
![AI](https://img.shields.io/badge/AI-LSTM%20AutoEncoder-red)

![Vision](https://img.shields.io/badge/Vision-OpenCV%20%2B%20RGB--D-green)

![Embedded](https://img.shields.io/badge/Embedded-STM32-orange)
![Embedded](https://img.shields.io/badge/Embedded-ESP32-green)
![Embedded](https://img.shields.io/badge/Embedded-Raspberry%20Pi-red)
![Protocol](https://img.shields.io/badge/Protocol-Modbus%20TCP-blue)

![Frontend](https://img.shields.io/badge/Frontend-Vue.js-42b883)
![Backend](https://img.shields.io/badge/Backend-Node.js-339933)
![Network](https://img.shields.io/badge/Network-WebSocket-purple)

<p align="center">
  <img src="./assets/system_overview.png" alt="System Overview">
</p>

This project implements an **intelligent robotic sorting system** that integrates **RGB-D vision, industrial robot control, embedded systems, predictive maintenance (PdM), and web-based monitoring**.

A Dobot manipulator performs **color-based object sorting** using an Intel RealSense D435i camera, while STM32/ESP32-based embedded devices handle **real-time signaling and safety control**. The overall system is coordinated through a **Modbus TCP–based industrial communication layer**, with additional support for **mobile robot (TurtleBot) interaction**.

In addition, a **web-based dashboard** provides **real-time visualization of system logs, Dobot status, and TurtleBot status** via WebSocket communication, enabling intuitive monitoring and operational awareness.

Furthermore, vibration data collected from the robot base is analyzed using an **LSTM AutoEncoder** to detect early signs of abnormal behavior, enabling **data-driven preventive maintenance** in a smart factory environment.

