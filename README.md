
# AI-Driven Health Management for Employees

## Overview

The **AI-Driven Health Management for Employees** module integrates OpenAI's LLM capabilities with the Odoo HR system to offer **intelligent health management tools**. This innovative solution enables organizations to support employee well-being, reduce absenteeism, and gain data-driven insights into workplace health.

This solution allows:
- **Employees** to describe symptoms and receive AI-driven preliminary health advice.
- **Organizations** to identify potential disease outbreaks, analyze risk trends, and provide preventive measures.

---

## Features

### Key Functionalities
1. **AI-Powered Diagnosis**:
   - Employees input symptoms and receive preliminary health advice via OpenAI's models.
   - Diagnoses structured in JSON for consistency.

2. **Symptom Checker**:
   - Provides suggestions for potential conditions and includes recommendations.

3. **Health Risk Scoring**:
   - Assigns risk scores (0-100) based on symptoms and historical data.
   - Provides escalation steps and risk analysis.

4. **Health Recommendations**:
   - Generates lifestyle suggestions and preventive measures using AI.

5. **Disease Outbreak Prediction**:
   - Aggregates data to predict potential outbreaks in the workplace.

6. **Comprehensive Reporting**:
   - Generate detailed health reports and dashboards.
   - Export data in various formats (e.g., CSV, Excel).

---

## Enhancements for Hackathon

### **Safety Enhancements**
- Implement anonymization of employee data for reports.
- Extend RBAC to control access to sensitive health data.
- Ensure compliance with GDPR by logging user consent.

### **Advanced Features**
- Build interactive dashboards to monitor:
  - Risk scoring trends.
  - Disease outbreak patterns.
- Add collaboration features for multi-agent analysis.

### **Benchmarking and Validation**
- Introduce tools to evaluate AI accuracy.
- Compare health trends over time for better decision-making.

### **Expanded AI Features**
- Calculate a severity index for symptoms.
- Introduce periodic revalidation of AI recommendations.

### **Enhanced Reporting**
- Add CSV/Excel export with configurable options.
- Improve inline editing for quick report adjustments.

### **Decentralized Collaboration**
- Develop APIs for integration with external systems.
- Enable live updates for trends among decentralized teams.

---

## Installation

1. Ensure your Odoo instance has the HR module installed.
2. Clone this repository into your Odoo `addons` directory:
   ```bash
   git clone https://github.com/elbasri/ai_health_management.git
   ```
3. Install the module from the Apps menu in Odoo.

---

## Configuration

1. Navigate to **Settings > Technical > Parameters > System Parameters**.
2. Set the following parameters:
   - `ai_health.openai_api_key`: Your OpenAI API key.
   - `ai_health.openai_model`: Preferred OpenAI model (e.g., `gpt-4`).

---

## Usage

1. **Symptom Reporting**:
   - Employees report symptoms through their profiles.
   - AI diagnoses are stored for review.

2. **Health Risk Analysis**:
   - HR managers assess risk scores and take preventive actions.

3. **Disease Outbreak Reports**:
   - Review aggregated predictions via analytics dashboards.

4. **Custom Reports**:
   - Export health, diagnosis, and risk data for organizational insights.

---

## Technical Details

The module includes the following components:
- **Controllers**: Handles API interactions.
- **Models**: Manages AI processing, diagnosis, and recommendations.
- **Views**: Provides user interfaces for data input and visualization.
- **Reports**: Offers detailed analysis and exportable formats.
- **Security**: Ensures role-based access and GDPR compliance.

---

## Requirements

- Odoo (Version: 13, 14, 15, 16, and 17)
- OpenAI API Key
- Internet connection for API calls

---

## Contributing

We welcome contributions to enhance the module. Please fork the repository, make your changes, and submit a pull request.

---

## License

This module is licensed under the AGPL-3. See the LICENSE file for more details.

---

## Author

Developed by **ABDENNACER Elbasri** | Twitter: **@abdennacerelb** | Linkedin **@elbasri**.
