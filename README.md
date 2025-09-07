# SmartPing

SmartPing is a lightweight, containerized network latency monitor inspired by [SmokePing](https://oss.oetiker.ch/smokeping/).  
It pings hosts at regular intervals, records results in SQLite, and displays latency/uptime in a simple web dashboard.

## Features
- Median latency measurement (burst of 20 pings every 5 minutes)
- Web dashboard built with Chart.js
- Add or remove hosts easily
- Fully containerized with Docker

## Usage

```bash
# Clone the repo
git clone https://github.com/chriskmurray/smartping.git
cd smartping

# Start containers
docker compose up --build
