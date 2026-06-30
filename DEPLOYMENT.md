# EC2 Deployment Guide

To deploy the World of Warships Stats Tracker to your Ubuntu EC2 instance with AWS RDS, follow these steps.

## 1. Prepare the EC2 Instance
SSH into your EC2 instance and install Docker and Docker Compose:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
```

## 2. Clone the Repository
```bash
git clone git@github.com:WilliamOnVoyage/World-of-Warships-Stats-Analysis.git
cd World-of-Warships-Stats-Analysis
```

## 3. Set up Environment Variables
Create a `.env` file inside the `backend/` directory:
```bash
nano backend/.env
```

Add the following variables. Crucially, set the `DATABASE_URL` to your new AWS RDS PostgreSQL endpoint:

```env
# AWS RDS Connection String
# Format: postgresql://[user]:[password]@[rds-endpoint]:5432/[db-name]
DATABASE_URL=postgresql://wows_admin:YourSecurePassword@your-rds-endpoint.us-east-1.rds.amazonaws.com:5432/wows_stats

# Wargaming API Application ID
WARGAMING_APP_ID=your_wargaming_api_key
```

## 4. Run the Application
Start the entire stack (Frontend, Backend API, and the continuous background Scraper) using Docker Compose:

```bash
sudo docker-compose up -d --build
```

- **Frontend:** Accessible on port `3000`.
- **Backend API:** Accessible on port `8000`.
- **Scraper:** Runs continuously in the background. It will automatically create the `Player` and `PlayerSnapshot` tables in your RDS instance on startup.

## 5. Check Scraper Logs
To ensure the scraper is successfully connecting to RDS and fetching Wargaming API data:
```bash
sudo docker-compose logs -f scraper
```
You should see it enumerating through the IDs and finding active players!
