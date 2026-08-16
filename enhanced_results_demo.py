"""
Demo script showing the enhanced results display system in action.

This demonstrates the integration of ResultsDisplayWidget and ActionButtonsFrame
for the KI Analysetool enhanced results processing feature.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from results_display import ResultsDisplayWidget
from action_buttons import ActionButtonsFrame


class EnhancedResultsDemo:
    """Demo application for enhanced results display system"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Results Display Demo")
        self.root.geometry("900x700")
        
        self.setup_ui()
        self.load_sample_content()
    
    def setup_ui(self):
        """Setup the demo UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Enhanced Results Display Demo", 
                               font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Content selection
        content_frame = ttk.LabelFrame(main_frame, text="Sample Content", padding=10)
        content_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Content type selection
        self.content_type_var = tk.StringVar(value="markdown")
        content_types = [("Markdown", "markdown"), ("Structured", "structured"), ("Plain", "plain")]
        
        for i, (label, value) in enumerate(content_types):
            ttk.Radiobutton(content_frame, text=label, variable=self.content_type_var,
                          value=value, command=self.on_content_type_change).grid(row=0, column=i, padx=10)
        
        # Sample content buttons
        button_frame = ttk.Frame(content_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Analysis Report", 
                  command=lambda: self.load_content("analysis")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Code Documentation", 
                  command=lambda: self.load_content("code")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Data Summary", 
                  command=lambda: self.load_content("data")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Research Paper", 
                  command=lambda: self.load_content("research")).pack(side=tk.LEFT, padx=5)
        
        # Results display widget
        display_frame = ttk.LabelFrame(main_frame, text="Enhanced Results Display", padding=5)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.results_display = ResultsDisplayWidget(display_frame)
        self.results_display.pack(fill=tk.BOTH, expand=True)
        
        # Action buttons frame
        actions_frame = ttk.LabelFrame(main_frame, text="Interactive Actions", padding=5)
        actions_frame.pack(fill=tk.X)
        
        self.action_buttons = ActionButtonsFrame(actions_frame, 
                                               on_action_callback=self.handle_action)
        self.action_buttons.pack(fill=tk.X)
    
    def load_sample_content(self):
        """Load initial sample content"""
        self.load_content("analysis")
    
    def load_content(self, content_type):
        """Load different types of sample content"""
        contents = {
            "analysis": self.get_analysis_content(),
            "code": self.get_code_content(),
            "data": self.get_data_content(),
            "research": self.get_research_content()
        }
        
        content = contents.get(content_type, contents["analysis"])
        display_type = self.content_type_var.get()
        
        # Update both widgets
        self.results_display.display_content(content, display_type)
        self.action_buttons.update_content(content, display_type)
    
    def on_content_type_change(self):
        """Handle content type change"""
        # Reload current content with new display type
        current_content = self.results_display.get_content()
        if current_content:
            display_type = self.content_type_var.get()
            self.results_display.display_content(current_content, display_type)
    
    def handle_action(self, action_name, content, content_type):
        """Handle action button clicks"""
        message = f"Action executed: {action_name}\n"
        message += f"Content type: {content_type}\n"
        message += f"Content length: {len(content)} characters\n"
        message += f"Content preview: {content[:100]}..."
        
        messagebox.showinfo("Action Executed", message)
    
    def get_analysis_content(self):
        """Get sample analysis content"""
        return """## Marktanalyse Q4 2024

### Zusammenfassung

Die Marktanalyse für das vierte Quartal 2024 zeigt **positive Entwicklungen** in mehreren Schlüsselbereichen:

- Umsatzsteigerung um 15,3% gegenüber Vorjahr
- Kundenzufriedenheit bei 4,2/5,0 Punkten
- Marktanteil gewachsen auf 23,7%

### Detaillierte Ergebnisse

#### Umsatzentwicklung
Der Gesamtumsatz erreichte €2.450.000, was einer Steigerung von 15,3% entspricht. Die wichtigsten Treiber waren:

1. **Produktlinie A**: +22% (€980.000)
2. **Produktlinie B**: +8% (€750.000)  
3. **Produktlinie C**: +12% (€720.000)

#### Kundenanalyse
- Neukunden: 1.247 (+18%)
- Wiederkehrende Kunden: 89,3%
- Durchschnittlicher Bestellwert: €156,80

### Empfehlungen

```
Prioritäten für Q1 2025:
1. Expansion in Produktlinie A
2. Verbesserung der Kundenbindung
3. Optimierung der Kostenstruktur
```

**Fazit**: Die Ergebnisse übertreffen die Erwartungen und bilden eine solide Grundlage für das kommende Jahr."""

    def get_code_content(self):
        """Get sample code documentation content"""
        return """## API Documentation

### User Authentication Module

This module handles user authentication and session management for the application.

#### Classes

##### AuthManager
```python
class AuthManager:
    def __init__(self, config):
        self.config = config
        self.sessions = {}
    
    def authenticate(self, username, password):
        \"\"\"Authenticate user credentials\"\"\"
        if self.validate_credentials(username, password):
            session_id = self.create_session(username)
            return {"success": True, "session_id": session_id}
        return {"success": False, "error": "Invalid credentials"}
    
    def validate_session(self, session_id):
        \"\"\"Validate active session\"\"\"
        return session_id in self.sessions
```

#### Functions

- `hash_password(password)`: Securely hash user passwords
- `generate_token()`: Generate secure session tokens
- `cleanup_expired_sessions()`: Remove expired sessions

#### Usage Example

```python
auth = AuthManager(config)
result = auth.authenticate("user@example.com", "password123")
if result["success"]:
    print(f"Login successful: {result['session_id']}")
```

#### Security Notes

⚠️ **Important**: Always use HTTPS in production environments.

- Passwords are hashed using bcrypt
- Sessions expire after 24 hours
- Rate limiting: 5 attempts per minute per IP"""

    def get_data_content(self):
        """Get sample data summary content"""
        return """## Sales Performance Dashboard

### Key Metrics (December 2024)

| Metric | Value | Change |
|--------|-------|--------|
| Total Revenue | €125,430 | +12.5% |
| Orders | 1,247 | +8.3% |
| Avg Order Value | €100.58 | +3.9% |
| Conversion Rate | 3.2% | +0.4% |

### Regional Performance

**Top Performing Regions:**
1. North: €45,200 (36.1%)
2. South: €38,750 (30.9%) 
3. East: €25,680 (20.5%)
4. West: €15,800 (12.6%)

### Product Categories

- Electronics: 45.2% (€56,694)
- Clothing: 28.7% (€35,998)
- Home & Garden: 16.8% (€21,072)
- Sports: 9.3% (€11,666)

### Customer Segments

**New vs Returning Customers:**
- New: 312 customers (25.0%)
- Returning: 935 customers (75.0%)

**Age Demographics:**
- 18-25: 18.5%
- 26-35: 32.1%
- 36-45: 28.9%
- 46-55: 15.2%
- 55+: 5.3%

### Trends & Insights

📈 **Growth Drivers:**
- Mobile sales increased 45%
- Email campaign CTR: 4.2%
- Social media referrals: +67%

📊 **Performance Indicators:**
- Customer satisfaction: 4.3/5.0
- Return rate: 2.1% (industry avg: 3.5%)
- Time to delivery: 2.3 days avg"""

    def get_research_content(self):
        """Get sample research paper content"""
        return """## The Impact of AI on Modern Business Processes

### Abstract

This study examines the transformative effects of artificial intelligence (AI) implementation on contemporary business operations. Through analysis of 150 companies across various sectors, we identify key performance improvements and implementation challenges.

### Introduction

Artificial intelligence has emerged as a critical technology for business transformation [1]. Recent studies indicate that 73% of enterprises plan to implement AI solutions by 2025 (McKinsey, 2024).

### Methodology

Our research employed a mixed-methods approach:
- **Quantitative Analysis**: Survey of 150 companies
- **Qualitative Research**: In-depth interviews with 25 executives
- **Case Studies**: Detailed analysis of 10 implementation projects

### Key Findings

#### Performance Improvements

1. **Operational Efficiency**: Average improvement of 34.2%
2. **Cost Reduction**: Mean savings of €2.3M annually
3. **Decision Speed**: 67% faster decision-making processes
4. **Customer Satisfaction**: Increased by 28% on average

#### Implementation Challenges

- **Technical Complexity**: 78% of respondents
- **Staff Training**: 65% of respondents  
- **Data Quality**: 59% of respondents
- **Integration Issues**: 52% of respondents

### Statistical Analysis

```python
# Sample correlation analysis
import pandas as pd
import numpy as np

# AI adoption vs performance metrics
correlation_matrix = np.array([
    [1.00, 0.73, 0.68, 0.45],
    [0.73, 1.00, 0.82, 0.56],
    [0.68, 0.82, 1.00, 0.61],
    [0.45, 0.56, 0.61, 1.00]
])
```

### Conclusions

The research demonstrates significant positive correlation between AI adoption and business performance metrics. However, successful implementation requires careful planning and substantial investment in training and infrastructure.

### References

[1] Smith, J. et al. (2024). "AI in Enterprise: A Comprehensive Study." *Journal of Business Technology*, 45(3), 123-145.

[2] https://www.mckinsey.com/ai-report-2024

[3] doi: 10.1000/ai-business-2024"""

    def run(self):
        """Run the demo application"""
        self.root.mainloop()


if __name__ == "__main__":
    demo = EnhancedResultsDemo()
    demo.run()