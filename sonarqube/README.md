# SonarQube Installation on EC2 (RHEL) for Jenkins Integration

This README describes how to install **SonarQube** on a **Red Hat Enterprise Linux** based **EC2 instance** and configure **Jenkins (version 2.504.3)** to use SonarQube in a CI/CD pipeline.

---

## 📌 Architecture Overview

| Component | Purpose |
|----------|---------|
| EC2 (RHEL) | Host for Jenkins & SonarQube |
| SonarQube | Code quality & security analysis |
| PostgreSQL | Backend DB for SonarQube |
| Jenkins | Executes pipeline & triggers Sonar scans |

SonarQube will run on **port 9000** and Jenkins on **port 8080** (if default).

---

## 🔧 1. Install System Dependencies

```bash
sudo yum update -y
sudo yum install -y java-17-openjdk java-17-openjdk-devel postgresql-server postgresql-contrib unzip wget
```

Verify Java:
```bash
java -version
```

---

## 🗄️ 2. Configure PostgreSQL

```bash
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo -u postgres psql

CREATE USER sonar WITH ENCRYPTED PASSWORD 'StrongPasswordHere';
CREATE DATABASE sonarqube OWNER sonar ENCODING 'UTF8';
GRANT ALL PRIVILEGES ON DATABASE sonarqube TO sonar;
\q
```

---

## 📦 3. Install SonarQube

```bash
cd /tmp
wget https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-<VERSION>.zip
unzip sonarqube-<VERSION>.zip
sudo mv sonarqube-<VERSION>/* /opt/sonarqube/
sudo useradd sonar
sudo chown -R sonar:sonar /opt/sonarqube
```

---

## ⚙️ 4. SonarQube Configuration

Update `/opt/sonarqube/conf/sonar.properties`:

```properties
sonar.jdbc.username=sonar
sonar.jdbc.password=StrongPasswordHere
sonar.jdbc.url=jdbc:postgresql://localhost/sonarqube
sonar.web.port=9000
```

Add Linux tuning parameters:

```bash
echo 'vm.max_map_count=524288' | sudo tee -a /etc/sysctl.conf
echo 'fs.file-max=131072' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## 🚀 5. Run SonarQube as a Service

Place included service file:

```bash
sudo cp sonarqube.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sonarqube
sudo systemctl start sonarqube
```

Check status:
```bash
systemctl status sonarqube
```

Access UI:
```
http://<EC2-IP>:9000
User: admin / admin
```

---

## 🔌 6. Jenkins Integration Steps

### Install Plugins
- SonarQube Scanner for Jenkins

### Configure SonarQube Server
Jenkins → Manage Jenkins → Configure System → SonarQube Servers

```
Name: sonarqube-local
URL: http://localhost:9000
Token: <Sonar Token>
```

### Add Scanner Tool
Manage Jenkins → Global Tool Configuration → SonarScanner

---

## 🧪 7. Jenkins Pipeline Example

See included `Jenkinsfile` for a working pipeline.

---

## 🔁 8. SonarQube Webhook

SonarQube → Administration → Configuration → Webhooks

```
http://<jenkins-url>/sonarqube-webhook/
```

Used for Quality Gate validation.

---

## 🎉 Success!

You now have a fully integrated **SonarQube + Jenkins** environment capable of analyzing code quality and enforcing build quality gates!

---
