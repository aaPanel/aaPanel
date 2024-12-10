<div align="center">
  <img src="https://www.aapanel.com/static/images/bt_logo.png" alt="aaPanel Logo" width="200"/>
  <h1>aaPanel - Professional Linux Panel</h1>
  <p>A simple but powerful hosting control panel for your Linux server</p>
</div>

<div align="center">

[![Docker Pulls](https://img.shields.io/docker/pulls/aapanel/aapanel.svg)](https://hub.docker.com/r/aapanel/aapanel)
[![Docker Stars](https://img.shields.io/docker/stars/aapanel/aapanel.svg)](https://hub.docker.com/r/aapanel/aapanel)
[![Docker Image Size](https://img.shields.io/docker/image-size/aapanel/aapanel)](https://hub.docker.com/r/aapanel/aapanel)
[![GitHub Stars](https://img.shields.io/github/stars/Rekt-Developer/aaPanel.svg?style=social)](https://github.com/Rekt-Developer/aaPanel)
[![GitHub Issues](https://img.shields.io/github/issues/Rekt-Developer/aaPanel.svg)](https://github.com/Rekt-Developer/aaPanel/issues)
[![GitHub Forks](https://img.shields.io/github/forks/Rekt-Developer/aaPanel.svg)](https://github.com/Rekt-Developer/aaPanel/network)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

## 📑 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Support](#support)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Introduction

aaPanel is a powerful and user-friendly control panel for managing your Linux server. With over 3,000,000 installations since 2017, it provides comprehensive tools for website management, hosting services, and server administration.

## ✨ Features

### Free Version
- 🌐 WP Toolkit Management
- 🔧 Website Management
- 📧 Mail Server Management
- 📁 FTP Management
- 🗄️ MySQL Management
- 📂 File Management
- 💻 Online Code Editor

### Pro Version
- 👥 Multi-User Account Management
- 🛡️ WAF (Web Application Firewall)
- 📊 Advanced Analytics
- 🔒 Enhanced File Protection
- 📨 Bulk Email Management

## 🏃 Quick Start

```bash
docker run -d \\
  -p 8886:8888 \\
  -p 22:21 \\
  -p 443:443 \\
  -p 80:80 \\
  -p 889:888 \\
  -v ~/website_data:/www/wwwroot \\
  -v ~/mysql_data:/www/server/data \\
  -v ~/vhost:/www/server/panel/vhost \\
  aapanel/aapanel:lib
```

## 🔧 Installation

### Default Access Information
- URL: `http://youripaddress:8886/`
- Username: `aapanel`
- Password: `aapanel123`

### Port Configuration
| Service | Port |
|---------|------|
| Control Panel | 8888 |
| PhpMyAdmin | 888 |
| HTTP | 80 |
| HTTPS | 443 |
| FTP | 21 |

### Directory Structure
| Purpose | Path |
|---------|------|
| Website Data | /www/wwwroot |
| MySQL Data | /www/server/data |
| Vhost Files | /www/server/panel/vhost |

## 📖 Documentation

For detailed documentation and guides, visit our [official website](https://www.aapanel.com).

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- 📧 Email: support@aapanel.com
- 🌐 Website: [www.aapanel.com](https://www.aapanel.com)
- 📝 Issues: [GitHub Issues](https://github.com/Rekt-Developer/aaPanel/issues)

---

<div align="center">
  <sub>Built with ❤️ by the aaPanel Team</sub>
</div>
