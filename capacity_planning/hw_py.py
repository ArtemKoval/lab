import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import linprog

# Sample data for 5 products
products = ['A', 'B', 'C', 'D', 'E']
demand_forecast = [1200, 800, 1500, 600, 900]  # Monthly units
profit_margins = [15, 22, 18, 25, 20]  # $ per unit
production_rates = [5, 3, 7, 4, 6]  # units per hour
machine_requirements = [2, 1, 3, 2, 1]  # machine hours per unit

# Resource constraints
total_machine_hours = 1600  # Monthly capacity
total_labor_hours = 1200    # Monthly capacity

# Create DataFrame for analysis
df = pd.DataFrame({
    'Product': products,
    'Demand': demand_forecast,
    'Margin': profit_margins,
    'Prod_Rate': production_rates,
    'Machine_Req': machine_requirements
})

# Calculate required resources for each product
df['Labor_Hours'] = df['Demand'] / df['Prod_Rate']
df['Machine_Hours'] = df['Demand'] * df['Machine_Req']
df['Total_Profit'] = df['Demand'] * df['Margin']

print("\nProduct Resource Requirements:")
print(df[['Product', 'Demand', 'Labor_Hours', 'Machine_Hours', 'Total_Profit']])

# Optimization to maximize profit within constraints
# Objective coefficients (negative for maximization)
c = -np.array(profit_margins)

# Constraint matrix
A = [
    [1/production_rates[0], 1/production_rates[1], 1/production_rates[2],
     1/production_rates[3], 1/production_rates[4]],  # Labor constraint
    [machine_requirements[0], machine_requirements[1], machine_requirements[2],
     machine_requirements[3], machine_requirements[4]]  # Machine constraint
]

# Constraint bounds
b = [total_labor_hours, total_machine_hours]

# Bounds for each product (0 <= x <= demand)
bounds = [(0, demand) for demand in demand_forecast]

# Solve linear programming problem
result = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')

# Create results DataFrame
optimized_production = pd.DataFrame({
    'Product': products,
    'Demand': demand_forecast,
    'Recommended_Production': result.x,
    'Unmet_Demand': demand_forecast - result.x,
    'Contribution': result.x * profit_margins
})

total_profit = optimized_production['Contribution'].sum()
labor_utilization = sum(result.x / production_rates) / total_labor_hours * 100
machine_utilization = sum(result.x * machine_requirements) / total_machine_hours * 100

print("\nOptimized Production Plan:")
print(optimized_production)
print(f"\nTotal Projected Profit: ${total_profit:,.2f}")
print(f"Labor Utilization: {labor_utilization:.1f}%")
print(f"Machine Utilization: {machine_utilization:.1f}%")

# Visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Production vs Demand
ax1.bar(optimized_production['Product'], optimized_production['Demand'],
        label='Demand', alpha=0.6)
ax1.bar(optimized_production['Product'], optimized_production['Recommended_Production'],
        label='Recommended Production', alpha=0.8)
ax1.set_title('Production vs Demand')
ax1.set_ylabel('Units')
ax1.legend()

# Resource utilization
resources = ['Labor', 'Machines']
utilization = [labor_utilization, machine_utilization]
ax2.bar(resources, utilization)
ax2.axhline(y=100, color='r', linestyle='--')
ax2.set_title('Resource Utilization')
ax2.set_ylabel('Utilization (%)')

plt.tight_layout()
plt.show()