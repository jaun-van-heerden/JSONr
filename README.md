# JSONr: JSON Recursive Resolver

A Python-based tool for recursively resolving JSON references across multiple files, enabling modular, scalable, and maintainable configurations.

## Features

- **Cross-File Resolution**: Dynamically resolves references (`$ref`) to external JSON files.
- **Recursive Resolution**: Supports nested and recursive references.
- **Lazy Loading with Caching**: Loads only required files and caches them for efficiency.
- **Circular Reference Detection**: Prevents infinite loops by detecting circular dependencies.
- **Schema Validation**: Ensures the final JSON structure conforms to a predefined JSON schema.
- **Tool-Agnostic**: Works with any JSON-based system and integrates easily into existing workflows.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/jsonr.git
   cd jsonr
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Example Input

#### Map File (`map.json`):
```json
{
  "base": "config/base.json",
  "network": "config/network.json"
}
```

#### Main JSON File (`main.json`):
```json
{
  "app": { "$ref": "base" },
  "network": { "$ref": "network" }
}
```

#### External Files:
- `config/base.json`:
  ```json
  {
    "name": "example-app",
    "version": "1.0.0"
  }
  ```

- `config/network.json`:
  ```json
  {
    "protocol": "MQTT",
    "host": "localhost"
  }
  ```

### Code Example
```python
from jsonr import JSONr

resolver = JSONr("map.json")
resolved_json = resolver.build("main.json")

print(resolved_json)
```

### Output:
```json
{
  "app": {
    "name": "example-app",
    "version": "1.0.0"
  },
  "network": {
    "protocol": "MQTT",
    "host": "localhost"
  }
}
```

---

## Use Cases

- **IoT Systems**: Modular configurations for sensors and devices.
- **Microservices**: Distributed service configurations with shared components.
- **Data Pipelines**: Reusable ETL workflow definitions.
- **Simulation Models**: Hierarchical data for scientific or industrial simulations.
- **CMS**: Dynamic content management with reusable references.

---

## Advantages

- **Modular and Scalable**: Split large configurations into reusable components.
- **Efficient**: Caches resolved files and supports lazy loading.
- **Safe**: Detects and prevents circular references.
- **Flexible**: Works in any JSON-based environment.

---

## Comparison Table

| Feature                          | JSON Schema  | YAML Anchors | Terraform Modules | JSONr                  |
|----------------------------------|--------------|--------------|-------------------|------------------------|
| Cross-File Resolution            | Limited      | No           | Yes               | Yes                    |
| Recursive Resolution             | No           | No           | Yes               | Yes                    |
| Lazy Loading                     | No           | No           | No                | Yes                    |
| Circular Reference Detection     | No           | No           | No                | Yes                    |
| General-Purpose (Not Domain-Specific) | Yes         | Yes          | No                | Yes                    |
| Dynamic and Modular Configuration | Limited      | Limited      | Yes               | Yes                    |

---

## Roadmap

Planned enhancements:
- **YAML Support**: Add support for YAML-based configurations.
- **Remote Fetching**: Resolve references from URLs or cloud storage.
- **CLI Tool**: Provide a command-line utility for resolution and validation.
- **Performance Optimizations**: Add parallel processing for large datasets.

---

## Contributing

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature-name"
   ```
4. Push to your branch and open a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
