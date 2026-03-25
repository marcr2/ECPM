# Economic Crisis Prediction Model (ECPM)

A data-driven platform that ingests US macroeconomic time-series data and translates it into the analytical categories of Marxist political economy — modeling, simulating, and forecasting the structural crisis tendencies inherent to capitalist accumulation.

Draws on the theoretical contributions of Marx, Engels, Lenin, Luxemburg, Leontief, and Beer to treat crises as endogenous expressions of capital's contradictions, not exogenous shocks.

## Architecture

ECPM uses a microservices architecture with 5 containerized services orchestrated via Docker Compose:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          External Data Sources                           │
│              FRED API  │  BEA API  │  Census API                         │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Celery Beat         │◀───── Scheduled Triggers
                    │  (Scheduler)         │       (Daily 6:00 AM ET)
                    └──────────┬───────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        Celery Worker Pool                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│  │ Data Fetch  │  │ Model Train  │  │ I-O Compute  │                    │
│  │ Tasks       │  │ Tasks        │  │ Tasks        │                    │
│  └─────────────┘  └──────────────┘  └──────────────┘                    │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  TimescaleDB   │◀──────┐
                  │  (PostgreSQL)  │       │
                  └────────┬───────┘       │
                           │               │
                           ▼               │
                  ┌────────────────┐       │
                  │     Redis      │       │
                  │  - Cache       │       │
                  │  - Broker      │       │
                  │  - Results     │       │
                  └────────┬───────┘       │
                           │               │
                           ▼               │
                  ┌────────────────┐       │
                  │  FastAPI       │───────┘
                  │  Backend       │
                  │  - REST API    │
                  │  - SSE Stream  │
                  └────────┬───────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  Next.js       │
                  │  Frontend      │
                  │  - Dashboard   │
                  │  - Charts      │
                  └────────────────┘
```

### Services

| Service           | Technology                  | Port | Purpose                                               |
|-------------------|-----------------------------|------|-------------------------------------------------------|
| **Backend**       | Python 3.12, FastAPI        | 8000 | REST API, SSE streaming, health checks                |
| **Celery Worker** | Python 3.12, Celery 5.6     | —    | Async task execution (fetch, train, compute)          |
| **Celery Beat**   | Python 3.12, Celery Beat    | —    | Scheduled task orchestration (6:00 AM + 6:05 AM ET)   |
| **Frontend**      | Next.js 16, React 19        | 3000 | Interactive dashboard (Tailwind + shadcn/ui)          |
| **Database**      | TimescaleDB (PostgreSQL 16) | 5432 | Time-series storage with hypertables                  |
| **Cache/Broker**  | Redis 7                     | 6379 | Response cache, Celery broker, result backend         |

### Data Flow

1. **Scheduled Ingestion**: Celery Beat triggers daily data fetch at 6:00 AM ET
2. **External APIs**: Celery workers pull data from FRED, BEA, and Census APIs
3. **Storage**: Raw observations stored in TimescaleDB hypertables
4. **Feature Engineering**: Computed indicators (rate of profit, OCC, etc.) cached on disk (24h) and selectively in Redis
5. **Model Training**: At 6:05 AM ET, VECM retrains on latest data
6. **API Layer**: FastAPI serves data, indicators, forecasts, and I-O analysis
7. **Frontend**: Next.js dashboard fetches via REST API, receives SSE notifications

## Crisis Mechanisms

The Composite Crisis Index synthesises three mechanism sub-indices, each aggregating related indicators:

1. **TRPF** (Marx) — Tendency of the rate of profit to fall via rising organic composition. Indicators: rate of profit (inverted), OCC, rate of surplus value (inverted), mass of profit.
2. **Realization crisis** (Luxemburg/Marx) — Surplus value cannot be realized in circulation. Indicator: productivity-wage gap.
3. **Financial fragility** (Marx Vol. III/Engels) — Credit and fictitious capital mask and amplify contradictions. Indicators: credit-to-GDP gap, financial-to-real asset ratio, debt service ratio.

## Modules

| # | Module                       | Status      | Description                                                            |
|---|------------------------------|-------------|------------------------------------------------------------------------|
| 1 | Data Ingestion               | Complete    | FRED/BEA/Census pipeline, TimescaleDB storage, scheduled fetching      |
| 2 | Feature Engineering          | Complete    | NIPA-to-Marx translation (Shaikh/Tonak + Kliman TSSI methodologies)    |
| 3 | Predictive Modeling          | Complete    | VECM forecasting, Composite Crisis Index, historical backtesting       |
| 4 | Structural Analysis          | Complete    | Leontief I-O, shock propagation, reproduction schema                   |
| 5 | Corporate Concentration      | Complete    | HHI/CR4/CR8 metrics, SEC EDGAR + Census data, trend analysis           |

## Features

### Phase 1: Data Ingestion
- **FRED API client** with 50+ macroeconomic series (GDP, employment, prices, interest rates)
- **BEA API client** for NIPA tables (national income, corporate profits, fixed assets)
- **Census API client** for Economic Census concentration data
- **Celery Beat scheduler** for automated daily data refresh
- **TimescaleDB storage** preserving native data frequencies

### Phase 2: Marxist Indicators
- **Rate of profit** computation with dual methodologies (Shaikh/Tonak current-cost, Kliman TSSI historical-cost)
- **Organic composition of capital** (constant capital / variable capital)
- **Rate of surplus value** (exploitation rate)
- **Mass of profit** (absolute surplus value)
- **Financial indicators**: credit-GDP gap, debt-service ratio, productivity-wage gap, financial-to-real asset ratio
- **Interactive comparison** of indicator values across methodologies
- **KaTeX formula rendering** showing computational derivations

### Phase 3: Predictive Modeling
- **VECM forecasting** with Johansen cointegration rank selection and up to 40-quarter horizon
- **Recursive residual bootstrap** confidence intervals (68% and 95% bands, 1 000 replications)
- **Composite Crisis Index** (0-100 scale) aggregating three mechanism sub-indices (TRPF, realization, financial fragility) with logistic-regression-learned weights
- **Historical backtesting** against 14 crisis episodes (1929-2023) with 12- and 24-month early-warning evaluation
- **Forecast overlay** on indicator charts with toggle controls
- **Auto-retraining** pipeline via Celery Beat with SSE progress streaming

### Phase 4: Structural Analysis
- **Leontief input-output analysis** from BEA Use/Make tables
- **Technical coefficient matrix** and **Leontief inverse** computation
- **Shock propagation simulation** — model sectoral demand shocks
- **Department I/II classification** (means of production vs. consumption goods)
- **Reproduction schema validation** (simple and expanded reproduction conditions)
- **Nivo heatmaps** for 71x71 I-O matrix visualization
- **Sankey diagrams** for inter-departmental flows

### Phase 5: Corporate Concentration
- **HHI (Herfindahl-Hirschman Index)** with DoJ/FTC threshold markers
- **CR4/CR8 concentration ratios** across NAICS industries
- **Trend analysis** tracking concentration over Census years
- **Lead-lag correlation** between concentration and Marxist indicators
- **Sparkline visualizations** for multi-industry comparison
- **Top correlated industries** identification

## Getting Started

### Prerequisites

**Required:**
- Docker Engine 24.0+ and Docker Compose V2
- [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) (free registration)
- [BEA API key](https://apps.bea.gov/API/signup/) (free registration)
- [Census API key](https://api.census.gov/data/key_signup.html) (free registration)

**Recommended:**
- 4GB+ RAM (8GB for structural I-O analysis)
- 10GB+ disk space
- Linux, macOS, or Windows with WSL2

### Quick Start (Development)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/ECPM.git
cd ECPM

# 2. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 3. Start all services
docker compose up

# 4. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

The initial startup will:
- Build Docker images (~5-10 minutes first time)
- Initialize TimescaleDB with hypertables
- Start Celery worker and beat scheduler
- Launch backend API and frontend dashboard

**First-time setup:**

```bash
# Trigger initial data fetch (instead of waiting for scheduled run)
curl -X POST http://localhost:8000/api/data/fetch

# Monitor Celery tasks
docker compose logs -f backend celery_worker celery_beat
```

Once healthy, services are available at:

| Service      | URL                        | Description                    |
|--------------|----------------------------|--------------------------------|
| Frontend     | http://localhost:3000      | Main dashboard                 |
| Backend API  | http://localhost:8000      | REST endpoints                 |
| API Docs     | http://localhost:8000/docs | Interactive Swagger UI         |
| TimescaleDB  | localhost:5432             | PostgreSQL connection          |
| Redis        | localhost:6379             | Cache/broker (development)     |

For **production deployment on Linux servers**, see the [Production Deployment](#production-deployment-linux) section below.

### Environment Variables

| Variable                | Default                                              | Description                   |
|-------------------------|------------------------------------------------------|-------------------------------|
| `FRED_API_KEY`          | —                                                    | FRED API key (required)       |
| `BEA_API_KEY`           | —                                                    | BEA API key (required)        |
| `CENSUS_API_KEY`        | —                                                    | Census API key (required)     |
| `DATABASE_URL`          | `postgresql+asyncpg://ecpm:ecpm_dev@timescaledb:5432/ecpm` | TimescaleDB connection  |
| `REDIS_URL`             | `redis://redis:6379/0`                               | Redis connection              |
| `CELERY_BROKER_URL`     | `redis://redis:6379/0`                               | Celery broker                 |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1`                               | Celery result backend         |
| `FETCH_SCHEDULE_HOUR`   | `6`                                                  | Daily fetch hour (UTC)        |
| `FETCH_SCHEDULE_MINUTE` | `0`                                                  | Daily fetch minute            |
| `LOG_LEVEL`             | `INFO`                                               | Logging level                 |

### Local Development (without Docker)

**Backend:**

```bash
cd backend
pip install -e ".[dev]"
pytest
uvicorn ecpm.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Requires TimescaleDB and Redis running locally or via `docker compose up timescaledb redis`.

## Production Deployment (Linux)

This guide covers production deployment on Linux systems (Ubuntu 22.04/24.04, Debian 12, Fedora, Arch, etc.).

### Prerequisites

**System Requirements:**
- Linux kernel 5.0+ (6.x recommended)
- 4GB RAM minimum (8GB+ recommended for large I-O computations)
- 20GB disk space (50GB+ recommended with data retention)
- Docker Engine 24.0+ and Docker Compose V2
- Nginx (for reverse proxy)
- certbot (for SSL/TLS)

**Install Docker (Ubuntu/Debian):**

```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt update
sudo apt install ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

**Install Docker (Fedora/RHEL/CentOS):**

```bash
sudo dnf install docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

**Install Docker (Arch Linux):**

```bash
sudo pacman -S docker docker-compose
sudo systemctl enable --now docker.service
sudo usermod -aG docker $USER
```

### Production Configuration

**1. Clone and configure environment:**

```bash
# Clone repository
git clone https://github.com/yourusername/ECPM.git /opt/ecpm
cd /opt/ecpm

# Create production environment file
cp .env.example .env.production

# Edit with secure credentials
nano .env.production
```

**2. Secure production `.env.production`:**

```bash
# Database credentials (use strong passwords)
POSTGRES_DB=ecpm
POSTGRES_USER=ecpm
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>
DATABASE_URL=postgresql+asyncpg://ecpm:<STRONG_PASSWORD_HERE>@timescaledb:5432/ecpm

# Redis (consider password protection in production)
REDIS_URL=redis://redis:6379/0

# API keys (never commit these)
FRED_API_KEY=<YOUR_FRED_API_KEY>
BEA_API_KEY=<YOUR_BEA_API_KEY>
CENSUS_API_KEY=<YOUR_CENSUS_API_KEY>

# Celery configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Schedule (UTC time, adjust for your timezone)
FETCH_SCHEDULE_HOUR=11  # 6 AM US/Eastern = 11 AM UTC
FETCH_SCHEDULE_MINUTE=0

# Logging
LOG_LEVEL=INFO
```

**3. Create production `docker-compose.prod.yml`:**

```bash
cat > docker-compose.prod.yml << 'EOF'
services:
  timescaledb:
    image: timescale/timescaledb:latest-pg16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - timescaledb_data:/var/lib/postgresql/data
      - ./config/timescaledb/init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ecpm_network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - ecpm_network

  backend:
    build:
      context: ./backend
    restart: unless-stopped
    command: uvicorn ecpm.main:app --host 0.0.0.0 --port 8000 --workers 4
    env_file:
      - .env.production
    depends_on:
      timescaledb:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ecpm_network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  celery_worker:
    build:
      context: ./backend
    restart: unless-stopped
    command: celery -A ecpm.tasks.celery_app worker --loglevel=info --concurrency=4
    env_file:
      - .env.production
    depends_on:
      timescaledb:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - ecpm_network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  celery_beat:
    build:
      context: ./backend
    restart: unless-stopped
    command: celery -A ecpm.tasks.celery_app beat --loglevel=info
    env_file:
      - .env.production
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - ecpm_network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: ./frontend
      args:
        - NODE_ENV=production
    restart: unless-stopped
    command: npm start
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ecpm_network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  ecpm_network:
    driver: bridge

volumes:
  timescaledb_data:
  redis_data:
EOF
```

**4. Start production services:**

```bash
# Build and start all services
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check service health
docker compose -f docker-compose.prod.yml ps
```

### Nginx Reverse Proxy

**1. Install Nginx:**

```bash
# Ubuntu/Debian
sudo apt install nginx

# Fedora/RHEL
sudo dnf install nginx

# Arch Linux
sudo pacman -S nginx
```

**2. Configure Nginx site:**

```bash
sudo nano /etc/nginx/sites-available/ecpm
```

```nginx
# /etc/nginx/sites-available/ecpm

upstream backend_api {
    server 127.0.0.1:8000;
}

upstream frontend_app {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name ecpm.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ecpm.yourdomain.com;

    # SSL certificates (managed by certbot)
    ssl_certificate /etc/letsencrypt/live/ecpm.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ecpm.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API endpoints
    location /api/ {
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }

    # API docs
    location /docs {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
    }

    # Health check
    location /health {
        proxy_pass http://backend_api;
        access_log off;
    }

    # Frontend application
    location / {
        proxy_pass http://frontend_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Next.js static files
    location /_next/static/ {
        proxy_pass http://frontend_app;
        proxy_cache_valid 200 365d;
        add_header Cache-Control "public, immutable";
    }

    # Client-side max body size for file uploads
    client_max_body_size 10M;
}
```

**3. Enable site and obtain SSL certificate:**

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ecpm /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Install certbot
sudo apt install certbot python3-certbot-nginx  # Ubuntu/Debian
# OR
sudo dnf install certbot python3-certbot-nginx  # Fedora

# Obtain SSL certificate
sudo certbot --nginx -d ecpm.yourdomain.com

# Reload Nginx
sudo systemctl reload nginx
```

### Systemd Service (Alternative to Docker Compose)

For systemd-based service management instead of `docker compose up -d`:

```bash
sudo nano /etc/systemd/system/ecpm.service
```

```ini
[Unit]
Description=ECPM Economic Crisis Prediction Model
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ecpm
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml --env-file .env.production up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml --env-file .env.production down
User=ecpm
Group=docker

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ecpm.service
sudo systemctl start ecpm.service

# Check status
sudo systemctl status ecpm.service
```

### Backup and Recovery

**1. Database backups (automated):**

```bash
# Create backup script
sudo nano /opt/ecpm/scripts/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/ecpm/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="ecpm-timescaledb-1"

mkdir -p $BACKUP_DIR

docker exec $CONTAINER_NAME pg_dump -U ecpm -Fc ecpm > \
    $BACKUP_DIR/ecpm_${TIMESTAMP}.dump

# Keep only last 7 days of backups
find $BACKUP_DIR -name "ecpm_*.dump" -mtime +7 -delete

echo "Backup completed: ecpm_${TIMESTAMP}.dump"
```

```bash
chmod +x /opt/ecpm/scripts/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /opt/ecpm/scripts/backup.sh >> /var/log/ecpm_backup.log 2>&1
```

**2. Restore from backup:**

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Start only database
docker compose -f docker-compose.prod.yml up -d timescaledb

# Restore backup
docker exec -i ecpm-timescaledb-1 pg_restore -U ecpm -d ecpm --clean < \
    /opt/ecpm/backups/ecpm_20260324_020000.dump

# Restart all services
docker compose -f docker-compose.prod.yml up -d
```

### Monitoring and Logging

**1. View application logs:**

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f celery_worker
docker compose -f docker-compose.prod.yml logs -f celery_beat

# JSON logs location
ls /var/lib/docker/containers/*/
```

**2. Monitor resource usage:**

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

**3. Health checks:**

```bash
# API health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Check all service health
docker compose -f docker-compose.prod.yml ps
```

### Performance Tuning

**1. PostgreSQL/TimescaleDB tuning (`config/timescaledb/postgresql.conf`):**

```ini
# Memory settings (adjust for your system)
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 64MB

# TimescaleDB settings
timescaledb.max_background_workers = 8

# Connection settings
max_connections = 100
```

**2. Redis tuning:**

```bash
# Add to docker-compose.prod.yml redis command
command: >
  redis-server
  --maxmemory 1gb
  --maxmemory-policy allkeys-lru
  --appendonly yes
  --save 60 1000
```

**3. Nginx caching:**

```nginx
# Add to /etc/nginx/nginx.conf http block
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

# Add to location /api/ block
proxy_cache api_cache;
proxy_cache_valid 200 5m;
proxy_cache_key "$scheme$request_method$host$request_uri";
add_header X-Cache-Status $upstream_cache_status;
```

### Firewall Configuration

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Firewalld (Fedora/RHEL)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### Troubleshooting

**Service won't start:**

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs timescaledb

# Verify environment variables
docker compose -f docker-compose.prod.yml config

# Check port conflicts
sudo netstat -tlnp | grep -E '(3000|8000|5432|6379)'
```

**Database connection errors:**

```bash
# Enter database container
docker exec -it ecpm-timescaledb-1 psql -U ecpm -d ecpm

# Check connections
SELECT * FROM pg_stat_activity;

# Verify TimescaleDB extension
\dx
```

**Celery tasks not running:**

```bash
# Check Celery worker logs
docker compose -f docker-compose.prod.yml logs celery_worker

# Check Beat scheduler logs
docker compose -f docker-compose.prod.yml logs celery_beat

# Inspect Redis
docker exec -it ecpm-redis-1 redis-cli
> PING
> KEYS celery*
```

## Project Structure

```
.
├── backend/
│   ├── ecpm/
│   │   ├── api/                      # FastAPI routers
│   │   │   ├── router.py             # Main router registration
│   │   │   ├── data.py               # Series data endpoints
│   │   │   ├── indicators.py         # Marxist indicator endpoints
│   │   │   ├── forecasting.py        # VAR/regime/crisis index endpoints
│   │   │   ├── structural.py         # I-O matrix and shock simulation
│   │   │   ├── concentration.py      # HHI/CR4 and correlation endpoints
│   │   │   └── status.py             # Health and pipeline status
│   │   ├── clients/                  # External API clients
│   │   │   ├── fred.py               # FRED API client
│   │   │   ├── bea.py                # BEA API client (NIPA + I-O)
│   │   │   └── census.py             # Census API client
│   │   ├── indicators/               # Marxist indicator computation
│   │   │   ├── base.py               # Base indicator framework
│   │   │   ├── shaikh_tonak.py       # Shaikh-Tonak methodology
│   │   │   ├── kliman.py             # Kliman TSSI methodology
│   │   │   └── financial.py          # Financial indicators (credit gap, etc.)
│   │   ├── modeling/                 # Predictive modeling
│   │   │   ├── vecm_model.py         # VECM fitting and forecasting
│   │   │   ├── crisis_index.py       # Composite Crisis Index
│   │   │   └── backtest.py           # Historical backtesting engine
│   │   ├── structural/               # Input-Output analysis
│   │   │   ├── leontief.py           # Leontief inverse computation
│   │   │   ├── departments.py        # Department I/II classification
│   │   │   ├── shock.py              # Shock propagation simulation
│   │   │   └── multipliers.py        # Output multipliers
│   │   ├── concentration/            # Corporate concentration analysis
│   │   │   ├── metrics.py            # HHI/CR4/CR8 computation
│   │   │   └── correlation.py        # Lead-lag correlation engine
│   │   ├── ingestion/                # ETL pipeline
│   │   │   ├── pipeline.py           # Main orchestrator
│   │   │   ├── fred_client.py        # FRED data ingestion
│   │   │   ├── bea_client.py         # BEA data ingestion
│   │   │   └── census_client.py      # Census data ingestion
│   │   ├── tasks/                    # Celery async tasks
│   │   │   ├── celery_app.py         # Celery config + beat schedule
│   │   │   ├── fetch_tasks.py        # Data fetch tasks
│   │   │   └── training_tasks.py     # Model training tasks
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── observation.py        # Time-series observation table
│   │   │   └── series_metadata.py    # Series metadata table
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   │   └── series.py             # Series data schemas
│   │   ├── core/                     # Core utilities
│   │   │   └── logging.py            # Structured logging (structlog)
│   │   ├── cache.py                  # Redis caching layer
│   │   ├── config.py                 # Pydantic settings (env vars)
│   │   ├── database.py               # Async SQLAlchemy session
│   │   ├── pipeline.py               # Pipeline orchestration
│   │   └── main.py                   # FastAPI app entry point
│   ├── tests/                        # pytest suite
│   │   ├── conftest.py               # Test fixtures
│   │   ├── test_api.py               # API endpoint tests
│   │   ├── test_fred_client.py       # FRED client tests
│   │   ├── test_bea_client.py        # BEA client tests
│   │   ├── test_ingestion_pipeline.py# Pipeline integration tests
│   │   ├── test_cache.py             # Cache layer tests
│   │   ├── test_models.py            # ORM model tests
│   │   └── test_tasks.py             # Celery task tests
│   ├── alembic/                      # Database migrations
│   │   └── versions/                 # Migration scripts
│   ├── Dockerfile                    # Backend container image
│   ├── pyproject.toml                # Python dependencies (PEP 621)
│   └── setup.py                      # Package metadata
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js 16 App Router
│   │   │   ├── page.tsx              # Dashboard home
│   │   │   ├── layout.tsx            # Root layout with sidebar
│   │   │   ├── indicators/           # Indicator charts + comparison
│   │   │   │   └── page.tsx
│   │   │   ├── forecasting/          # VECM forecasts + crisis index
│   │   │   │   └── page.tsx
│   │   │   ├── structural/           # I-O matrix + shock simulation
│   │   │   │   └── page.tsx
│   │   │   └── concentration/        # HHI/CR4 + correlation
│   │   │       └── page.tsx
│   │   ├── components/               # React components
│   │   │   ├── data/                 # Data fetching/display
│   │   │   ├── layout/               # Sidebar, header, navigation
│   │   │   ├── charts/               # Recharts + Nivo wrappers
│   │   │   ├── ui/                   # shadcn/ui components
│   │   │   └── indicators/           # Indicator-specific components
│   │   └── lib/                      # Utilities
│   │       ├── api-client.ts         # Backend API client
│   │       └── utils.ts              # Helper functions
│   ├── public/                       # Static assets
│   ├── Dockerfile                    # Frontend container image
│   ├── package.json                  # Node dependencies
│   ├── tsconfig.json                 # TypeScript config
│   └── tailwind.config.ts            # Tailwind CSS config
├── config/
│   └── timescaledb/
│       └── init.sql                  # TimescaleDB initialization
├── docs/
│   └── ECPM_Architecture.md          # Theoretical framework
├── .planning/                        # Development planning (GSD workflow)
│   ├── PROJECT.md                    # Project overview
│   ├── ROADMAP.md                    # Phase breakdown
│   ├── STATE.md                      # Current state
│   ├── COMPLETION_CHECKLIST.md       # v1.0 completion criteria
│   └── phases/                       # Phase-specific plans
├── docker-compose.yml                # Base service definitions
├── docker-compose.override.yml       # Development overrides
├── docker-compose.prod.yml           # Production configuration (create this)
├── .env.example                      # Environment template
├── .env.production                   # Production secrets (DO NOT COMMIT)
├── CHANGELOG.md                      # Release notes
├── README.md                         # This file
└── LICENSE                           # MIT License
```

### Key Directories

- **`backend/ecpm/api/`**: FastAPI route handlers, organized by domain (data, indicators, forecasting, structural, concentration)
- **`backend/ecpm/tasks/`**: Celery async tasks for scheduled data fetch (6:00 AM) and model retraining (6:05 AM)
- **`backend/ecpm/indicators/`**: Core Marxist indicator logic (rate of profit, OCC, s/v) with multiple methodologies
- **`backend/ecpm/modeling/`**: Econometric forecasting (VECM) and Composite Crisis Index
- **`backend/ecpm/structural/`**: Leontief I-O analysis, shock propagation, reproduction schema
- **`backend/ecpm/concentration/`**: HHI/CR4/CR8 metrics and lead-lag correlation analysis
- **`frontend/src/app/`**: Next.js pages with App Router (server + client components)
- **`frontend/src/components/ui/`**: shadcn/ui component library (buttons, cards, tables, dialogs)
- **`config/timescaledb/`**: PostgreSQL init scripts for hypertable creation

## API Endpoints

### Data Ingestion
- `GET /api/data/series` — List all series metadata
- `GET /api/data/series/{series_id}` — Get series observations
- `POST /api/data/fetch` — Trigger manual data fetch

### Indicators
- `GET /api/indicators` — List all indicator summaries
- `GET /api/indicators/{slug}` — Get indicator time series
- `GET /api/indicators/{slug}/compare` — Compare across methodologies
- `GET /api/indicators/methodologies` — List methodology documentation

### Forecasting
- `GET /api/forecasting/forecasts` — Get VECM forecast results
- `GET /api/forecasting/regime` — Get current regime detection
- `GET /api/forecasting/crisis-index` — Get composite crisis index
- `GET /api/forecasting/backtests` — Get historical backtest results
- `POST /api/forecasting/train` — Trigger model retraining

### Structural Analysis
- `GET /api/structural/years` — Available I-O table years
- `GET /api/structural/matrix/{year}` — Get coefficient or inverse matrix
- `POST /api/structural/shock` — Run shock simulation
- `GET /api/structural/reproduction/{year}` — Get Dept I/II flows
- `GET /api/structural/critical-sectors/{year}` — Identify critical sectors

### Concentration Analysis
- `GET /api/concentration/industries` — List industries with concentration data
- `GET /api/concentration/{naics}/metrics` — Get HHI/CR4/CR8 for industry
- `GET /api/concentration/trends` — Get concentration trends over time
- `GET /api/concentration/correlations` — Get correlation with indicators

## License

[MIT](LICENSE)
