# CAI/RF Analysis - Current vs CMS Official Methodology

## **📊 WHAT WE CURRENTLY CALCULATE**

### **In Our App (`static/app.js` lines 451-488):**

```javascript
function calculateMetrics() {
    let weightedSum = 0;
    let totalWeight = 0;
    
    measures.forEach(measure => {
        if (measure.star_rating) {
            weightedSum += measure.star_rating * measure.weight;
            totalWeight += measure.weight;
        }
    });
    
    const weightedAvg = weightedSum / totalWeight;
}
```

### **Our Current Formula:**
```
Weighted Avg Star = Σ(Measure Star × Measure Weight) / Σ(Measure Weight)
```

**Example:**
- C01: 4 stars × 1 weight = 4
- C12: 5 stars × 3 weight = 15
- C14: 3 stars × 3 weight = 9
- Total: (4+15+9) / (1+3+3) = 28 / 7 = **4.00 stars**

### **What This Gives Us:**
✅ **Simple weighted average of measure stars**
❌ **Does NOT include:**
- Domain-level aggregation
- CAI adjustment (socioeconomic)
- Reward Factor (consistency bonus)
- Improvement measure logic (C30/D04)

---

## **🎯 CMS OFFICIAL METHODOLOGY (from Technical Notes)**

### **Step 1: Calculate Domain Averages**
Group measures into 5 domains (HD1-HD5 for Part C, DD1-DD4 for Part D):

```
HD1 (Staying Healthy) = Avg of C01-C06 stars
HD2 (Managing Chronic) = Avg of C07-C21 stars
HD3 (Member Experience) = Avg of C22-C27 stars
HD4 (Complaints/Changes) = Avg of C28-C30 stars
HD5 (Customer Service) = Avg of C31-C33 stars
```

### **Step 2: Calculate Weighted Summary Rating**
```
Part C Summary = (HD1×3 + HD2×3 + HD3×2 + HD4×2 + HD5×1)
```

### **Step 3: Apply CAI Adjustment**

**CAI (Categorical Adjustment Index)** adjusts for socioeconomic mix:
- Based on % LIS/DE (Low Income Subsidy / Dual Eligible) beneficiaries
- Based on % Disabled beneficiaries
- **CAI values range from -0.3 to +0.4**

**From the CAI CSV you provided:**
```csv
Contract,Part C FAC,Part D MA-PD FAC,Overall FAC
H0028,4,3,4          ← CAI category 4 for Overall
H0034,7,5,8          ← CAI category 8 for Overall
H0107,1,1,1          ← CAI category 1 for Overall
```

**CAI Adjustment Categories (from Table 12 in Tech Notes):**
```
Category 1: High LIS/DE + High Disability    → CAI = +0.4
Category 2-3: Medium-High                     → CAI = +0.2 to +0.3
Category 4-5: Medium                          → CAI = +0.1
Category 6-7: Medium-Low                      → CAI = -0.1
Category 8-9: Low LIS/DE + Low Disability     → CAI = -0.2 to -0.3
```

**Example:**
- Raw Part C Summary = 3.85
- Contract has CAI category 4 (Overall FAC=4) → CAI = +0.1
- **Adjusted Part C Summary = 3.85 + 0.1 = 3.95**

### **Step 4: Apply Reward Factor (r-Factor)**

**Reward Factor** rewards consistency across measures:
- Calculated as: `r = mean + (0.5 × sqrt(variance))`
- Rewards contracts with high, consistent performance
- **Can add up to ~0.4 stars**

**Formula:**
```
variance = Σ[weight × (star - mean)²] / Σ(weight)
r-Factor = mean + 0.5 × √variance
```

**Example:**
- Mean = 4.0
- If all measures are exactly 4 stars → variance = 0 → r-Factor = 4.0 + 0 = 4.0
- If measures vary (3,4,5 stars) → variance = 0.67 → r-Factor = 4.0 + 0.41 = 4.41

### **Step 5: Apply Improvement Measures (C30/D04)**

**Special logic for high performers:**
- Calculate rating WITH and WITHOUT improvement measures
- **If contract has ≥4 stars:** Use whichever is higher (don't penalize)
- **If contract has <4 stars:** Always include improvement measures

### **Step 6: Round to Final Star**

**Rounding Rules:**
```
< 2.25 → 2.0 stars
2.25 - 2.75 → 2.5 stars
2.75 - 3.25 → 3.0 stars
3.25 - 3.75 → 3.5 stars
3.75 - 4.25 → 4.0 stars
4.25 - 4.75 → 4.5 stars
≥ 4.75 → 5.0 stars
```

---

## **🔢 FULL EXAMPLE: H0028 (Humana)**

### **From CAI CSV:**
```
Contract: H0028
Part C FAC: 4
Part D MA-PD FAC: 3
Overall FAC: 4
```

### **Step-by-Step Calculation:**

#### **1. Calculate Domain Averages** (hypothetical)
```
HD1 = 4.2 stars
HD2 = 3.8 stars
HD3 = 4.0 stars
HD4 = 3.5 stars
HD5 = 4.5 stars
```

#### **2. Calculate Weighted Summary**
```
Part C Summary = (4.2×3 + 3.8×3 + 4.0×2 + 3.5×2 + 4.5×1) / 11
               = (12.6 + 11.4 + 8.0 + 7.0 + 4.5) / 11
               = 43.5 / 11
               = 3.95 (before CAI)
```

#### **3. Apply CAI**
```
CAI Category 4 → CAI = +0.1
Part C Summary = 3.95 + 0.1 = 4.05
```

#### **4. Apply Reward Factor**
```
variance = 0.18 (measures vary slightly)
r-Factor = 4.05 + 0.5 × √0.18 = 4.05 + 0.21 = 4.26
```

#### **5. Apply Improvement Measure (C30)**
```
With C30: 4.26
Without C30: 4.30
Contract has ≥4 stars → Use higher: 4.30
```

#### **6. Round to Final Star**
```
4.30 falls in range 4.25-4.75 → **4.5 stars** (final)
```

---

## **📉 GAP ANALYSIS: What We're Missing**

| Feature | Our App | CMS Official | Impact |
|---------|---------|--------------|--------|
| **Measure Stars** | ✅ Have it | ✅ | - |
| **Measure Weights** | ✅ Have it | ✅ | - |
| **Domain Grouping** | ❌ Missing | ✅ | -0.1 to +0.1 stars |
| **CAI Adjustment** | ❌ Missing | ✅ | **-0.3 to +0.4 stars** |
| **Reward Factor** | ❌ Missing | ✅ | **0 to +0.4 stars** |
| **Improvement Logic** | ❌ Missing | ✅ | 0 to +0.2 stars |
| **Proper Rounding** | ❌ Missing | ✅ | Can change final star |

### **Total Potential Error: -0.3 to +1.0 stars**

---

## **🗂️ DATA WE HAVE**

### **CAI CSV Structure:**
```csv
Contract Number,Part C FAC,Part D MA-PD FAC,Part D PDP FAC,Overall FAC
H0028,4,3,N/A,4
H0034,7,5,N/A,8
```

- **FAC = Final Adjustment Category** (1-9 for Overall, 1-8 for Part C, etc.)
- This maps to specific CAI values per the technical notes tables

### **High/Low Performing CSVs:**
```csv
Contract Number,Rated As,Highest Rating,Rating
H1290,MA-PD,Overall,5
```
- Shows which contracts achieved 5-star status
- Can cross-reference with our calculations

---

## **✅ NEXT STEPS TO IMPLEMENT**

### **Phase 1: Add CAI Adjustment** (Highest Impact)
1. Load CAI CSV into backend (`api.py`)
2. Map FAC categories to CAI values per technical notes tables
3. Add CAI to summary/overall calculations
4. Display adjusted vs unadjusted ratings

### **Phase 2: Add Reward Factor**
1. Calculate variance of measure stars
2. Apply r-Factor formula
3. Show consistency bonus

### **Phase 3: Add Improvement Measure Logic**
1. Implement "with/without" C30/D04 comparison
2. Apply ≥4 star protection rule

### **Phase 4: Proper Rounding**
1. Apply CMS rounding rules to final ratings

---

## **🎯 PRIORITY RECOMMENDATION**

**Start with CAI** - it has the biggest impact (-0.3 to +0.4 stars) and we have all the data we need!

Would you like me to implement CAI adjustment first?

