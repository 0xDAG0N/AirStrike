# Airstrike.dev

The official landing page and documentation site for **[Airstrike](https://github.com/mahmoud-sadder/airstrike)**, the advanced Wi-Fi penetration testing toolkit.

This repository hosts the static website source code for [airstrike.dev](https://airstrike.dev).

## 🚀 Tech Stack

- **HTML5**: Semantic markup for accessibility and SEO.
- **CSS3**: Custom styling with variables for theming (Vanilla CSS).
- **JavaScript**: Vanilla JS for interactive elements (navigation, dynamic updates).

## 🛠️ Local Development

To run this website locally, you just need a static file server.

### Using Python
```bash
# Run inside the project directory
python3 -m http.server 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### Using Node.js (npx)
```bash
npx serve .
```

### Using Docker 🐳

#### Build and Run with Docker

Build the Docker image:
```bash
docker build -t airstrike-web .
```

Run the container:
```bash
docker run -p 8000:8000 airstrike-web
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

#### Using Docker Compose

For a simpler one-command setup:
```bash
docker-compose up
```

This will build the image and start the container. Access the site at [http://localhost:8000](http://localhost:8000).

To stop the container:
```bash
docker-compose down
```

## 🤝 Contributing

We welcome contributions to improve the documentation or the site's design!

1.  **Fork** the repository.
2.  Create a new **branch** for your feature or fix.
3.  **Commit** your changes.
4.  Push to your fork and submit a **Pull Request**.

> **Note**: If you are looking to contribute to the **Airstrike tool itself** (Python code), please visit the [main repository](https://github.com/mahmoud-sadder/airstrike).

## 🔗 Links

- **Main Tool Repository**: [mahmoud-sadder/airstrike](https://github.com/mahmoud-sadder/airstrike)
- **Live Website**: [airstrike.dev](https://airstrike.dev)
- **Issue Tracker**: [GitHub Issues](https://github.com/mahmoud-sadder/airstrike.dev/issues)

## 📄 License

This website content is open source. See the LICENSE file for details.
