# 🕵️ OSINT Web Application

This project is a Dockerized full-stack web application for Open-Source Intelligence (OSINT) domain reconnaissance. It allows users to input a domain (e.g., `example.com`) and runs two powerful tools – `theHarvester` and `Amass` – to gather information like subdomains, emails, IP addresses, and more. Results are presented via a clean React interface, stored persistently, and exportable to Excel.

## 📦 Project Structure

```
project-root/
├── front/         # React Frontend (UI)
├── server/        # FastAPI Backend (API)
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### 🛠️ Requirements

Make sure you have the following installed on your machine:

- Docker: https://docs.docker.com/get-docker/
- Docker Compose: https://docs.docker.com/compose/install/
- Git (optional but recommended): https://git-scm.com/

### 📥 Installation

Clone the repository and navigate into the project folder:

```bash
git clone https://github.com/YZohar8/OSINT.git
cd OSINT
```

> Or if you have this as a ZIP file, just extract it and `cd` into the directory.

### ▶️ Run the App

Use the following one-liner to build and start everything:

```bash
docker-compose up --build
```

This will:
- Build both frontend and backend containers.
- Start both services using Docker Compose.

### 🌐 Access the App

- React UI: [http://localhost:3000](http://localhost:3000)
- FastAPI API (dev): [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing

Tests will be added in future versions.

---

## 📁 Deliverables

This repository includes:

- `front/`: React-based UI.
- `server/`: FastAPI backend with scanning endpoints.
- `docker-compose.yml`: Central orchestration file.
- `README.md`: Project overview and instructions.

---
