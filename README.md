# aaPanel - The Ultimate Hosting Control Panel

[![Docker Pulls](https://img.shields.io/docker/pulls/aapanel/aapanel.svg?style=for-the-badge)](https://hub.docker.com/r/aapanel/aapanel)
[![License](https://img.shields.io/github/license/aapanel/aaPanel.svg?style=for-the-badge)](https://github.com/aapanel/aaPanel/blob/master/LICENSE)

aaPanel is a powerful, user-friendly hosting control panel designed to revolutionize server management. With its sleek interface and extensive feature set, aaPanel has become a go-to choice for web developers and hosting providers worldwide.

## Key Features

- **Open-Source Freedom:** aaPanel is open-source, allowing customization and community contributions.
- **Intuitive Interface:** Enjoy a modern, user-friendly control panel for efficient server management.
- **Comprehensive Management:** Effortlessly manage websites, databases, email, FTP, and more.
- **WP Toolkit Integration:** Optimize your WordPress sites with the built-in WP Toolkit.
- **Enhanced Security:** Protect your server with WAF and file protection features.
- **Scalability:** Support for shared hosting and multiple user accounts.
- **Bulk Email Sending:** Send emails in bulk for marketing and newsletters.

## Getting Started

### Docker Deployment

aaPanel's official Docker image simplifies deployment. Follow these steps:

```bash
# Pull the aaPanel Docker image
$ docker pull aapanel/aapanel:lib

# Run aaPanel with the following command
$ docker run -d \
  -p 8886:8888 \
  -p 22:21 \
  -p 443:443 \
  -p 80:80 \
  -p 889:888 \
  -v ~/website_data:/www/wwwroot \
  -v ~/mysql_data:/www/server/data \
  -v ~/vhost:/www/server/panel/vhost \
  aapanel/aapanel:lib
```

Access aaPanel at `http://youripaddress:8886/`.

**Default Credentials:**
- Username: `aapanel`
- Password: `aapanel123` (Change immediately!)

### Port Usage

- Control Panel: `8888`
- PhpMyAdmin: `888`

### Directory Structure

- Website Data: `/www/wwwroot`
- Mysql Data: `/www/server/data`
- Vhost File: `/www/server/panel/vhost`

## Upgrade to Paid Version

Unlock additional features and support by upgrading to the paid version:

1. Log in to aaPanel.
2. Navigate to "Settings."
3. Choose "Upgrade" and follow the process.

## Community and Support

Join the aaPanel community for support and collaboration:

- [aaPanel Forum](https://www.aapanel.com/forum/)
- [GitHub Issues](https://github.com/aapanel/aaPanel/issues)

## Contributing

We value your contributions! Follow our [Contribution Guidelines](https://github.com/aapanel/aaPanel/blob/master/CONTRIBUTING.md) to get involved.

## License

aaPanel is licensed under the [MIT License](https://github.com/aapanel/aaPanel/blob/master/LICENSE).

## Installation Guide

For detailed installation instructions, refer to our [Installation Guide](https://github.com/Rekt-Developer/aaPanel/blob/master/INSTALL.md).

---

# Installation Index

This repository houses the aaPanel Docker image. To begin, follow the [README.md](https://github.com/Rekt-Developer/aaPanel/blob/master/README.md) for deployment. For comprehensive guides, visit the [aaPanel Documentation](https://www.aapanel.com/doc/).

```
