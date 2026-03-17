"""
Build all research data files for Portfolio Risk Exposure Analyzer.
Run from: C:/Users/rafil/Documents/portfolio-risk-analyzer/
"""

import json
import math
import os
import openpyxl
import warnings

warnings.filterwarnings("ignore")

RESEARCH_DIR = "research"

# ──────────────────────────────────────────────────────────────────────────────
# TASK 1: DAMODARAN BETAS
# ──────────────────────────────────────────────────────────────────────────────

DAMODARAN_RAW = [
    {"industry": "Advertising", "num_firms": 52, "levered_beta": 1.21, "de_ratio_pct": 40.20, "tax_rate_pct": 5.02, "unlevered_beta": 0.93, "cash_firm_value_pct": 7.73, "unlevered_beta_cash_adj": 1.01, "hilo_risk": 0.6233, "std_dev_equity_pct": 62.91, "std_dev_op_income_pct": 15.17},
    {"industry": "Aerospace/Defense", "num_firms": 79, "levered_beta": 0.95, "de_ratio_pct": 15.56, "tax_rate_pct": 11.58, "unlevered_beta": 0.85, "cash_firm_value_pct": 2.61, "unlevered_beta_cash_adj": 0.87, "hilo_risk": 0.5213, "std_dev_equity_pct": 46.45, "std_dev_op_income_pct": 21.86},
    {"industry": "Air Transport", "num_firms": 23, "levered_beta": 1.19, "de_ratio_pct": 91.17, "tax_rate_pct": 8.29, "unlevered_beta": 0.70, "cash_firm_value_pct": 7.11, "unlevered_beta_cash_adj": 0.76, "hilo_risk": 0.5152, "std_dev_equity_pct": 59.00, "std_dev_op_income_pct": 210.43},
    {"industry": "Apparel", "num_firms": 35, "levered_beta": 0.94, "de_ratio_pct": 31.29, "tax_rate_pct": 9.61, "unlevered_beta": 0.76, "cash_firm_value_pct": 4.60, "unlevered_beta_cash_adj": 0.79, "hilo_risk": 0.5786, "std_dev_equity_pct": 46.26, "std_dev_op_income_pct": 26.80},
    {"industry": "Auto & Truck", "num_firms": 33, "levered_beta": 1.46, "de_ratio_pct": 19.70, "tax_rate_pct": 3.74, "unlevered_beta": 1.27, "cash_firm_value_pct": 2.99, "unlevered_beta_cash_adj": 1.31, "hilo_risk": 0.7242, "std_dev_equity_pct": 61.83, "std_dev_op_income_pct": 38.88},
    {"industry": "Auto Parts", "num_firms": 35, "levered_beta": 1.34, "de_ratio_pct": 41.46, "tax_rate_pct": 15.00, "unlevered_beta": 1.02, "cash_firm_value_pct": 9.45, "unlevered_beta_cash_adj": 1.13, "hilo_risk": 0.5243, "std_dev_equity_pct": 49.87, "std_dev_op_income_pct": 21.22},
    {"industry": "Bank (Money Center)", "num_firms": 15, "levered_beta": 0.76, "de_ratio_pct": 164.19, "tax_rate_pct": 18.43, "unlevered_beta": 0.34, "cash_firm_value_pct": 23.17, "unlevered_beta_cash_adj": 0.44, "hilo_risk": 0.2310, "std_dev_equity_pct": 22.74, "std_dev_op_income_pct": None},
    {"industry": "Banks (Regional)", "num_firms": 568, "levered_beta": 0.40, "de_ratio_pct": 52.10, "tax_rate_pct": 17.61, "unlevered_beta": 0.29, "cash_firm_value_pct": 23.48, "unlevered_beta_cash_adj": 0.37, "hilo_risk": 0.1917, "std_dev_equity_pct": 22.68, "std_dev_op_income_pct": 55.33},
    {"industry": "Beverage (Alcoholic)", "num_firms": 14, "levered_beta": 0.81, "de_ratio_pct": 43.34, "tax_rate_pct": 12.35, "unlevered_beta": 0.61, "cash_firm_value_pct": 2.37, "unlevered_beta_cash_adj": 0.63, "hilo_risk": 0.5830, "std_dev_equity_pct": 55.96, "std_dev_op_income_pct": 18.74},
    {"industry": "Beverage (Soft)", "num_firms": 27, "levered_beta": 0.64, "de_ratio_pct": 20.59, "tax_rate_pct": 6.85, "unlevered_beta": 0.56, "cash_firm_value_pct": 3.44, "unlevered_beta_cash_adj": 0.58, "hilo_risk": 0.6187, "std_dev_equity_pct": 57.89, "std_dev_op_income_pct": 18.65},
    {"industry": "Broadcasting", "num_firms": 24, "levered_beta": 0.47, "de_ratio_pct": 85.85, "tax_rate_pct": 7.73, "unlevered_beta": 0.29, "cash_firm_value_pct": 9.18, "unlevered_beta_cash_adj": 0.32, "hilo_risk": 0.5721, "std_dev_equity_pct": 46.62, "std_dev_op_income_pct": 24.68},
    {"industry": "Brokerage & Investment Banking", "num_firms": 32, "levered_beta": 1.17, "de_ratio_pct": 135.57, "tax_rate_pct": 15.27, "unlevered_beta": 0.58, "cash_firm_value_pct": 14.51, "unlevered_beta_cash_adj": 0.68, "hilo_risk": 0.4221, "std_dev_equity_pct": 36.61, "std_dev_op_income_pct": None},
    {"industry": "Building Materials", "num_firms": 41, "levered_beta": 1.11, "de_ratio_pct": 26.00, "tax_rate_pct": 18.02, "unlevered_beta": 0.93, "cash_firm_value_pct": 3.16, "unlevered_beta_cash_adj": 0.96, "hilo_risk": 0.4099, "std_dev_equity_pct": 35.28, "std_dev_op_income_pct": 38.06},
    {"industry": "Business & Consumer Services", "num_firms": 155, "levered_beta": 0.89, "de_ratio_pct": 19.72, "tax_rate_pct": 10.38, "unlevered_beta": 0.77, "cash_firm_value_pct": 4.02, "unlevered_beta_cash_adj": 0.81, "hilo_risk": 0.5302, "std_dev_equity_pct": 41.11, "std_dev_op_income_pct": 27.10},
    {"industry": "Cable TV", "num_firms": 9, "levered_beta": 0.74, "de_ratio_pct": 146.94, "tax_rate_pct": 10.64, "unlevered_beta": 0.35, "cash_firm_value_pct": 2.89, "unlevered_beta_cash_adj": 0.36, "hilo_risk": 0.4441, "std_dev_equity_pct": 44.04, "std_dev_op_income_pct": 26.88},
    {"industry": "Chemical (Basic)", "num_firms": 29, "levered_beta": 1.01, "de_ratio_pct": 99.35, "tax_rate_pct": 7.68, "unlevered_beta": 0.58, "cash_firm_value_pct": 8.91, "unlevered_beta_cash_adj": 0.64, "hilo_risk": 0.5354, "std_dev_equity_pct": 45.81, "std_dev_op_income_pct": 39.28},
    {"industry": "Chemical (Diversified)", "num_firms": 4, "levered_beta": 0.85, "de_ratio_pct": 176.11, "tax_rate_pct": 0.00, "unlevered_beta": 0.37, "cash_firm_value_pct": 9.75, "unlevered_beta_cash_adj": 0.41, "hilo_risk": 0.4230, "std_dev_equity_pct": 39.04, "std_dev_op_income_pct": 45.64},
    {"industry": "Chemical (Specialty)", "num_firms": 59, "levered_beta": 0.97, "de_ratio_pct": 29.88, "tax_rate_pct": 13.68, "unlevered_beta": 0.79, "cash_firm_value_pct": 3.91, "unlevered_beta_cash_adj": 0.82, "hilo_risk": 0.4095, "std_dev_equity_pct": 42.31, "std_dev_op_income_pct": 21.76},
    {"industry": "Coal & Related Energy", "num_firms": 16, "levered_beta": 1.07, "de_ratio_pct": 7.14, "tax_rate_pct": 3.13, "unlevered_beta": 1.02, "cash_firm_value_pct": 14.03, "unlevered_beta_cash_adj": 1.18, "hilo_risk": 0.6619, "std_dev_equity_pct": 64.31, "std_dev_op_income_pct": 242.50},
    {"industry": "Computer Services", "num_firms": 64, "levered_beta": 1.09, "de_ratio_pct": 25.10, "tax_rate_pct": 10.53, "unlevered_beta": 0.92, "cash_firm_value_pct": 4.80, "unlevered_beta_cash_adj": 0.96, "hilo_risk": 0.5715, "std_dev_equity_pct": 53.43, "std_dev_op_income_pct": 19.63},
    {"industry": "Computers/Peripherals", "num_firms": 36, "levered_beta": 1.35, "de_ratio_pct": 4.62, "tax_rate_pct": 5.91, "unlevered_beta": 1.31, "cash_firm_value_pct": 1.47, "unlevered_beta_cash_adj": 1.32, "hilo_risk": 0.5571, "std_dev_equity_pct": 54.58, "std_dev_op_income_pct": 30.57},
    {"industry": "Construction Supplies", "num_firms": 40, "levered_beta": 1.15, "de_ratio_pct": 17.62, "tax_rate_pct": 16.04, "unlevered_beta": 1.02, "cash_firm_value_pct": 2.94, "unlevered_beta_cash_adj": 1.05, "hilo_risk": 0.4302, "std_dev_equity_pct": 35.51, "std_dev_op_income_pct": 38.60},
    {"industry": "Diversified", "num_firms": 20, "levered_beta": 0.88, "de_ratio_pct": 15.55, "tax_rate_pct": 2.76, "unlevered_beta": 0.79, "cash_firm_value_pct": 6.42, "unlevered_beta_cash_adj": 0.84, "hilo_risk": 0.5558, "std_dev_equity_pct": 28.41, "std_dev_op_income_pct": 69.90},
    {"industry": "Drugs (Biotechnology)", "num_firms": 496, "levered_beta": 1.14, "de_ratio_pct": 13.04, "tax_rate_pct": 1.08, "unlevered_beta": 1.03, "cash_firm_value_pct": 4.20, "unlevered_beta_cash_adj": 1.08, "hilo_risk": 0.6431, "std_dev_equity_pct": 75.68, "std_dev_op_income_pct": 40.52},
    {"industry": "Drugs (Pharmaceutical)", "num_firms": 228, "levered_beta": 0.98, "de_ratio_pct": 14.54, "tax_rate_pct": 2.99, "unlevered_beta": 0.89, "cash_firm_value_pct": 3.16, "unlevered_beta_cash_adj": 0.92, "hilo_risk": 0.6841, "std_dev_equity_pct": 76.64, "std_dev_op_income_pct": 26.77},
    {"industry": "Education", "num_firms": 32, "levered_beta": 0.78, "de_ratio_pct": 24.38, "tax_rate_pct": 15.54, "unlevered_beta": 0.66, "cash_firm_value_pct": 8.26, "unlevered_beta_cash_adj": 0.72, "hilo_risk": 0.5006, "std_dev_equity_pct": 47.24, "std_dev_op_income_pct": 37.79},
    {"industry": "Electrical Equipment", "num_firms": 112, "levered_beta": 1.25, "de_ratio_pct": 12.00, "tax_rate_pct": 4.82, "unlevered_beta": 1.15, "cash_firm_value_pct": 3.53, "unlevered_beta_cash_adj": 1.19, "hilo_risk": 0.6771, "std_dev_equity_pct": 72.71, "std_dev_op_income_pct": 19.79},
    {"industry": "Electronics (Consumer & Office)", "num_firms": 8, "levered_beta": 0.87, "de_ratio_pct": 5.80, "tax_rate_pct": 0.00, "unlevered_beta": 0.83, "cash_firm_value_pct": 10.52, "unlevered_beta_cash_adj": 0.93, "hilo_risk": 0.6314, "std_dev_equity_pct": 70.18, "std_dev_op_income_pct": None},
    {"industry": "Electronics (General)", "num_firms": 114, "levered_beta": 0.97, "de_ratio_pct": 11.01, "tax_rate_pct": 8.04, "unlevered_beta": 0.90, "cash_firm_value_pct": 4.28, "unlevered_beta_cash_adj": 0.94, "hilo_risk": 0.5332, "std_dev_equity_pct": 51.84, "std_dev_op_income_pct": 25.55},
    {"industry": "Engineering/Construction", "num_firms": 48, "levered_beta": 1.21, "de_ratio_pct": 14.01, "tax_rate_pct": 13.64, "unlevered_beta": 1.09, "cash_firm_value_pct": 3.74, "unlevered_beta_cash_adj": 1.14, "hilo_risk": 0.4819, "std_dev_equity_pct": 45.92, "std_dev_op_income_pct": 40.66},
    {"industry": "Entertainment", "num_firms": 92, "levered_beta": 0.83, "de_ratio_pct": 15.91, "tax_rate_pct": 3.30, "unlevered_beta": 0.74, "cash_firm_value_pct": 3.36, "unlevered_beta_cash_adj": 0.76, "hilo_risk": 0.6108, "std_dev_equity_pct": 48.71, "std_dev_op_income_pct": 33.72},
    {"industry": "Environmental & Waste Services", "num_firms": 53, "levered_beta": 0.95, "de_ratio_pct": 21.45, "tax_rate_pct": 4.27, "unlevered_beta": 0.81, "cash_firm_value_pct": 1.25, "unlevered_beta_cash_adj": 0.82, "hilo_risk": 0.6040, "std_dev_equity_pct": 54.91, "std_dev_op_income_pct": 33.05},
    {"industry": "Farming/Agriculture", "num_firms": 35, "levered_beta": 1.13, "de_ratio_pct": 51.85, "tax_rate_pct": 6.29, "unlevered_beta": 0.81, "cash_firm_value_pct": 3.87, "unlevered_beta_cash_adj": 0.85, "hilo_risk": 0.5709, "std_dev_equity_pct": 50.79, "std_dev_op_income_pct": 49.70},
    {"industry": "Financial Svcs. (Non-bank & Insurance)", "num_firms": 176, "levered_beta": 0.97, "de_ratio_pct": 272.13, "tax_rate_pct": 12.06, "unlevered_beta": 0.32, "cash_firm_value_pct": 2.69, "unlevered_beta_cash_adj": 0.33, "hilo_risk": 0.4484, "std_dev_equity_pct": 42.47, "std_dev_op_income_pct": 33.72},
    {"industry": "Food Processing", "num_firms": 78, "levered_beta": 0.61, "de_ratio_pct": 43.73, "tax_rate_pct": 10.37, "unlevered_beta": 0.46, "cash_firm_value_pct": 2.56, "unlevered_beta_cash_adj": 0.47, "hilo_risk": 0.4859, "std_dev_equity_pct": 43.47, "std_dev_op_income_pct": 9.38},
    {"industry": "Food Wholesalers", "num_firms": 13, "levered_beta": 0.87, "de_ratio_pct": 46.97, "tax_rate_pct": 9.15, "unlevered_beta": 0.64, "cash_firm_value_pct": 1.06, "unlevered_beta_cash_adj": 0.65, "hilo_risk": 0.5105, "std_dev_equity_pct": 33.98, "std_dev_op_income_pct": 35.62},
    {"industry": "Furn/Home Furnishings", "num_firms": 27, "levered_beta": 0.82, "de_ratio_pct": 42.33, "tax_rate_pct": 11.38, "unlevered_beta": 0.62, "cash_firm_value_pct": 4.19, "unlevered_beta_cash_adj": 0.65, "hilo_risk": 0.4719, "std_dev_equity_pct": 51.51, "std_dev_op_income_pct": 20.43},
    {"industry": "Green & Renewable Energy", "num_firms": 15, "levered_beta": 0.86, "de_ratio_pct": 113.11, "tax_rate_pct": 0.00, "unlevered_beta": 0.46, "cash_firm_value_pct": 1.90, "unlevered_beta_cash_adj": 0.47, "hilo_risk": 0.7310, "std_dev_equity_pct": 65.14, "std_dev_op_income_pct": 28.78},
    {"industry": "Healthcare Products", "num_firms": 204, "levered_beta": 0.91, "de_ratio_pct": 12.79, "tax_rate_pct": 4.85, "unlevered_beta": 0.83, "cash_firm_value_pct": 3.25, "unlevered_beta_cash_adj": 0.86, "hilo_risk": 0.5590, "std_dev_equity_pct": 61.79, "std_dev_op_income_pct": 30.90},
    {"industry": "Healthcare Support Services", "num_firms": 104, "levered_beta": 0.87, "de_ratio_pct": 35.43, "tax_rate_pct": 9.80, "unlevered_beta": 0.69, "cash_firm_value_pct": 7.51, "unlevered_beta_cash_adj": 0.74, "hilo_risk": 0.5230, "std_dev_equity_pct": 47.24, "std_dev_op_income_pct": 24.13},
    {"industry": "Healthcare Information and Technology", "num_firms": 115, "levered_beta": 1.11, "de_ratio_pct": 15.74, "tax_rate_pct": 6.38, "unlevered_beta": 0.99, "cash_firm_value_pct": 2.46, "unlevered_beta_cash_adj": 1.02, "hilo_risk": 0.5788, "std_dev_equity_pct": 63.78, "std_dev_op_income_pct": 35.53},
    {"industry": "Homebuilding", "num_firms": 30, "levered_beta": 0.91, "de_ratio_pct": 21.34, "tax_rate_pct": 16.99, "unlevered_beta": 0.78, "cash_firm_value_pct": 8.00, "unlevered_beta_cash_adj": 0.85, "hilo_risk": 0.3682, "std_dev_equity_pct": 32.79, "std_dev_op_income_pct": 59.59},
    {"industry": "Hospitals/Healthcare Facilities", "num_firms": 31, "levered_beta": 0.80, "de_ratio_pct": 59.92, "tax_rate_pct": 11.35, "unlevered_beta": 0.55, "cash_firm_value_pct": 2.32, "unlevered_beta_cash_adj": 0.56, "hilo_risk": 0.5198, "std_dev_equity_pct": 56.46, "std_dev_op_income_pct": 20.29},
    {"industry": "Hotel/Gaming", "num_firms": 63, "levered_beta": 1.08, "de_ratio_pct": 39.75, "tax_rate_pct": 8.31, "unlevered_beta": 0.83, "cash_firm_value_pct": 4.96, "unlevered_beta_cash_adj": 0.88, "hilo_risk": 0.4804, "std_dev_equity_pct": 39.65, "std_dev_op_income_pct": 99.05},
    {"industry": "Household Products", "num_firms": 110, "levered_beta": 0.82, "de_ratio_pct": 18.15, "tax_rate_pct": 6.50, "unlevered_beta": 0.72, "cash_firm_value_pct": 3.14, "unlevered_beta_cash_adj": 0.74, "hilo_risk": 0.6273, "std_dev_equity_pct": 55.46, "std_dev_op_income_pct": 12.19},
    {"industry": "Information Services", "num_firms": 15, "levered_beta": 0.92, "de_ratio_pct": 33.17, "tax_rate_pct": 18.16, "unlevered_beta": 0.74, "cash_firm_value_pct": 2.54, "unlevered_beta_cash_adj": 0.76, "hilo_risk": 0.4395, "std_dev_equity_pct": 32.38, "std_dev_op_income_pct": 40.82},
    {"industry": "Insurance (General)", "num_firms": 21, "levered_beta": 0.67, "de_ratio_pct": 25.63, "tax_rate_pct": 12.77, "unlevered_beta": 0.56, "cash_firm_value_pct": 2.50, "unlevered_beta_cash_adj": 0.58, "hilo_risk": 0.4201, "std_dev_equity_pct": 46.07, "std_dev_op_income_pct": 42.10},
    {"industry": "Insurance (Life)", "num_firms": 20, "levered_beta": 0.64, "de_ratio_pct": 67.84, "tax_rate_pct": 15.19, "unlevered_beta": 0.43, "cash_firm_value_pct": 19.67, "unlevered_beta_cash_adj": 0.53, "hilo_risk": 0.2318, "std_dev_equity_pct": 35.15, "std_dev_op_income_pct": 28.26},
    {"industry": "Insurance (Prop/Cas.)", "num_firms": 57, "levered_beta": 0.48, "de_ratio_pct": 14.83, "tax_rate_pct": 18.37, "unlevered_beta": 0.44, "cash_firm_value_pct": 4.68, "unlevered_beta_cash_adj": 0.46, "hilo_risk": 0.2677, "std_dev_equity_pct": 28.70, "std_dev_op_income_pct": 37.90},
    {"industry": "Investments & Asset Management", "num_firms": 283, "levered_beta": 0.66, "de_ratio_pct": 32.69, "tax_rate_pct": 3.53, "unlevered_beta": 0.53, "cash_firm_value_pct": 9.92, "unlevered_beta_cash_adj": 0.59, "hilo_risk": 0.2498, "std_dev_equity_pct": 30.04, "std_dev_op_income_pct": 23.01},
    {"industry": "Machinery", "num_firms": 105, "levered_beta": 0.96, "de_ratio_pct": 14.69, "tax_rate_pct": 13.37, "unlevered_beta": 0.87, "cash_firm_value_pct": 2.91, "unlevered_beta_cash_adj": 0.89, "hilo_risk": 0.4387, "std_dev_equity_pct": 45.03, "std_dev_op_income_pct": 23.40},
    {"industry": "Metals & Mining", "num_firms": 73, "levered_beta": 1.04, "de_ratio_pct": 10.98, "tax_rate_pct": 2.52, "unlevered_beta": 0.96, "cash_firm_value_pct": 4.63, "unlevered_beta_cash_adj": 1.01, "hilo_risk": 0.7047, "std_dev_equity_pct": 77.56, "std_dev_op_income_pct": 53.67},
    {"industry": "Office Equipment & Services", "num_firms": 14, "levered_beta": 1.33, "de_ratio_pct": 48.10, "tax_rate_pct": 12.30, "unlevered_beta": 0.98, "cash_firm_value_pct": 5.55, "unlevered_beta_cash_adj": 1.04, "hilo_risk": 0.4265, "std_dev_equity_pct": 39.61, "std_dev_op_income_pct": 14.22},
    {"industry": "Oil/Gas (Integrated)", "num_firms": 4, "levered_beta": 0.30, "de_ratio_pct": 13.85, "tax_rate_pct": 28.24, "unlevered_beta": 0.27, "cash_firm_value_pct": 2.44, "unlevered_beta_cash_adj": 0.28, "hilo_risk": 0.1572, "std_dev_equity_pct": 20.27, "std_dev_op_income_pct": 106.56},
    {"industry": "Oil/Gas (Production and Exploration)", "num_firms": 142, "levered_beta": 0.72, "de_ratio_pct": 37.59, "tax_rate_pct": 6.66, "unlevered_beta": 0.56, "cash_firm_value_pct": 2.73, "unlevered_beta_cash_adj": 0.58, "hilo_risk": 0.5045, "std_dev_equity_pct": 42.22, "std_dev_op_income_pct": 185.49},
    {"industry": "Oil/Gas Distribution", "num_firms": 23, "levered_beta": 0.67, "de_ratio_pct": 58.53, "tax_rate_pct": 9.17, "unlevered_beta": 0.47, "cash_firm_value_pct": 0.89, "unlevered_beta_cash_adj": 0.47, "hilo_risk": 0.4565, "std_dev_equity_pct": 42.24, "std_dev_op_income_pct": 56.92},
    {"industry": "Oilfield Svcs/Equip.", "num_firms": 97, "levered_beta": 0.95, "de_ratio_pct": 37.36, "tax_rate_pct": 8.75, "unlevered_beta": 0.74, "cash_firm_value_pct": 5.59, "unlevered_beta_cash_adj": 0.79, "hilo_risk": 0.4766, "std_dev_equity_pct": 48.32, "std_dev_op_income_pct": 82.21},
    {"industry": "Packaging & Container", "num_firms": 19, "levered_beta": 1.02, "de_ratio_pct": 55.11, "tax_rate_pct": 15.57, "unlevered_beta": 0.72, "cash_firm_value_pct": 3.46, "unlevered_beta_cash_adj": 0.75, "hilo_risk": 0.3815, "std_dev_equity_pct": 25.45, "std_dev_op_income_pct": 13.14},
    {"industry": "Paper/Forest Products", "num_firms": 6, "levered_beta": 0.96, "de_ratio_pct": 43.69, "tax_rate_pct": 8.60, "unlevered_beta": 0.72, "cash_firm_value_pct": 6.25, "unlevered_beta_cash_adj": 0.77, "hilo_risk": 0.4671, "std_dev_equity_pct": 56.94, "std_dev_op_income_pct": 67.29},
    {"industry": "Power", "num_firms": 46, "levered_beta": 0.48, "de_ratio_pct": 74.15, "tax_rate_pct": 12.75, "unlevered_beta": 0.31, "cash_firm_value_pct": 1.45, "unlevered_beta_cash_adj": 0.31, "hilo_risk": 0.2234, "std_dev_equity_pct": 25.38, "std_dev_op_income_pct": 17.04},
    {"industry": "Precious Metals", "num_firms": 56, "levered_beta": 0.84, "de_ratio_pct": 7.28, "tax_rate_pct": 5.97, "unlevered_beta": 0.79, "cash_firm_value_pct": 4.53, "unlevered_beta_cash_adj": 0.83, "hilo_risk": 0.7327, "std_dev_equity_pct": 69.95, "std_dev_op_income_pct": 67.60},
    {"industry": "Publishing & Newspapers", "num_firms": 19, "levered_beta": 0.56, "de_ratio_pct": 23.94, "tax_rate_pct": 10.21, "unlevered_beta": 0.48, "cash_firm_value_pct": 6.75, "unlevered_beta_cash_adj": 0.51, "hilo_risk": 0.3069, "std_dev_equity_pct": 35.93, "std_dev_op_income_pct": 12.15},
    {"industry": "R.E.I.T.", "num_firms": 190, "levered_beta": 0.64, "de_ratio_pct": 84.46, "tax_rate_pct": 1.58, "unlevered_beta": 0.39, "cash_firm_value_pct": 1.91, "unlevered_beta_cash_adj": 0.40, "hilo_risk": 0.2593, "std_dev_equity_pct": 26.37, "std_dev_op_income_pct": 23.20},
    {"industry": "Real Estate (Development)", "num_firms": 14, "levered_beta": 0.84, "de_ratio_pct": 101.83, "tax_rate_pct": 4.91, "unlevered_beta": 0.48, "cash_firm_value_pct": 15.21, "unlevered_beta_cash_adj": 0.56, "hilo_risk": 0.6070, "std_dev_equity_pct": 52.10, "std_dev_op_income_pct": 81.39},
    {"industry": "Real Estate (General/Diversified)", "num_firms": 12, "levered_beta": 0.81, "de_ratio_pct": 53.56, "tax_rate_pct": 4.65, "unlevered_beta": 0.58, "cash_firm_value_pct": 7.83, "unlevered_beta_cash_adj": 0.63, "hilo_risk": 0.4625, "std_dev_equity_pct": 31.21, "std_dev_op_income_pct": 46.67},
    {"industry": "Real Estate (Operations & Services)", "num_firms": 54, "levered_beta": 0.97, "de_ratio_pct": 24.64, "tax_rate_pct": 8.70, "unlevered_beta": 0.81, "cash_firm_value_pct": 4.98, "unlevered_beta_cash_adj": 0.86, "hilo_risk": 0.4308, "std_dev_equity_pct": 50.56, "std_dev_op_income_pct": 29.71},
    {"industry": "Recreation", "num_firms": 49, "levered_beta": 1.02, "de_ratio_pct": 62.99, "tax_rate_pct": 11.45, "unlevered_beta": 0.70, "cash_firm_value_pct": 5.62, "unlevered_beta_cash_adj": 0.74, "hilo_risk": 0.5365, "std_dev_equity_pct": 48.31, "std_dev_op_income_pct": 25.09},
    {"industry": "Reinsurance", "num_firms": 1, "levered_beta": 0.58, "de_ratio_pct": 43.47, "tax_rate_pct": 30.36, "unlevered_beta": 0.44, "cash_firm_value_pct": 24.11, "unlevered_beta_cash_adj": 0.58, "hilo_risk": 0.1880, "std_dev_equity_pct": 19.21, "std_dev_op_income_pct": 21.97},
    {"industry": "Restaurant/Dining", "num_firms": 64, "levered_beta": 0.92, "de_ratio_pct": 27.22, "tax_rate_pct": 9.92, "unlevered_beta": 0.77, "cash_firm_value_pct": 1.99, "unlevered_beta_cash_adj": 0.78, "hilo_risk": 0.4914, "std_dev_equity_pct": 41.15, "std_dev_op_income_pct": 22.10},
    {"industry": "Retail (Automotive)", "num_firms": 34, "levered_beta": 0.94, "de_ratio_pct": 45.36, "tax_rate_pct": 10.77, "unlevered_beta": 0.70, "cash_firm_value_pct": 2.08, "unlevered_beta_cash_adj": 0.71, "hilo_risk": 0.4825, "std_dev_equity_pct": 44.58, "std_dev_op_income_pct": 29.76},
    {"industry": "Retail (Building Supply)", "num_firms": 14, "levered_beta": 1.54, "de_ratio_pct": 23.29, "tax_rate_pct": 11.84, "unlevered_beta": 1.31, "cash_firm_value_pct": 0.81, "unlevered_beta_cash_adj": 1.32, "hilo_risk": 0.3865, "std_dev_equity_pct": 45.88, "std_dev_op_income_pct": 28.49},
    {"industry": "Retail (Distributors)", "num_firms": 62, "levered_beta": 0.95, "de_ratio_pct": 28.24, "tax_rate_pct": 14.59, "unlevered_beta": 0.78, "cash_firm_value_pct": 2.36, "unlevered_beta_cash_adj": 0.80, "hilo_risk": 0.4330, "std_dev_equity_pct": 39.29, "std_dev_op_income_pct": 38.70},
    {"industry": "Retail (General)", "num_firms": 23, "levered_beta": 0.81, "de_ratio_pct": 7.94, "tax_rate_pct": 19.10, "unlevered_beta": 0.76, "cash_firm_value_pct": 2.68, "unlevered_beta_cash_adj": 0.78, "hilo_risk": 0.3806, "std_dev_equity_pct": 43.34, "std_dev_op_income_pct": 37.61},
    {"industry": "Retail (Grocery and Food)", "num_firms": 15, "levered_beta": 1.12, "de_ratio_pct": 51.95, "tax_rate_pct": 12.22, "unlevered_beta": 0.80, "cash_firm_value_pct": 5.14, "unlevered_beta_cash_adj": 0.85, "hilo_risk": 0.4158, "std_dev_equity_pct": 49.42, "std_dev_op_income_pct": 33.40},
    {"industry": "Retail (REITs)", "num_firms": 26, "levered_beta": 0.62, "de_ratio_pct": 56.42, "tax_rate_pct": 1.60, "unlevered_beta": 0.44, "cash_firm_value_pct": 1.48, "unlevered_beta_cash_adj": 0.44, "hilo_risk": 0.2005, "std_dev_equity_pct": 18.77, "std_dev_op_income_pct": 16.63},
    {"industry": "Retail (Special Lines)", "num_firms": 94, "levered_beta": 1.09, "de_ratio_pct": 19.76, "tax_rate_pct": 10.07, "unlevered_beta": 0.95, "cash_firm_value_pct": 5.30, "unlevered_beta_cash_adj": 1.00, "hilo_risk": 0.5309, "std_dev_equity_pct": 53.25, "std_dev_op_income_pct": 25.77},
    {"industry": "Rubber & Tires", "num_firms": 3, "levered_beta": 0.53, "de_ratio_pct": 358.47, "tax_rate_pct": 0.00, "unlevered_beta": 0.14, "cash_firm_value_pct": 7.01, "unlevered_beta_cash_adj": 0.15, "hilo_risk": 0.3628, "std_dev_equity_pct": 50.77, "std_dev_op_income_pct": 61.96},
    {"industry": "Semiconductor", "num_firms": 66, "levered_beta": 1.52, "de_ratio_pct": 2.59, "tax_rate_pct": 5.11, "unlevered_beta": 1.49, "cash_firm_value_pct": 1.02, "unlevered_beta_cash_adj": 1.50, "hilo_risk": 0.5440, "std_dev_equity_pct": 55.83, "std_dev_op_income_pct": 41.94},
    {"industry": "Semiconductor Equip", "num_firms": 31, "levered_beta": 1.40, "de_ratio_pct": 4.86, "tax_rate_pct": 9.96, "unlevered_beta": 1.35, "cash_firm_value_pct": 3.13, "unlevered_beta_cash_adj": 1.39, "hilo_risk": 0.4760, "std_dev_equity_pct": 50.08, "std_dev_op_income_pct": 49.58},
    {"industry": "Shipbuilding & Marine", "num_firms": 8, "levered_beta": 0.75, "de_ratio_pct": 22.55, "tax_rate_pct": 5.26, "unlevered_beta": 0.64, "cash_firm_value_pct": 2.54, "unlevered_beta_cash_adj": 0.66, "hilo_risk": 0.5291, "std_dev_equity_pct": 50.09, "std_dev_op_income_pct": 70.60},
    {"industry": "Shoe", "num_firms": 11, "levered_beta": 1.02, "de_ratio_pct": 11.94, "tax_rate_pct": 11.86, "unlevered_beta": 0.93, "cash_firm_value_pct": 6.65, "unlevered_beta_cash_adj": 1.00, "hilo_risk": 0.4536, "std_dev_equity_pct": 50.08, "std_dev_op_income_pct": 26.37},
    {"industry": "Software (Entertainment)", "num_firms": 77, "levered_beta": 1.03, "de_ratio_pct": 2.04, "tax_rate_pct": 5.29, "unlevered_beta": 1.01, "cash_firm_value_pct": 0.78, "unlevered_beta_cash_adj": 1.02, "hilo_risk": 0.6091, "std_dev_equity_pct": 57.06, "std_dev_op_income_pct": 59.01},
    {"industry": "Software (Internet)", "num_firms": 29, "levered_beta": 1.69, "de_ratio_pct": 12.30, "tax_rate_pct": 3.05, "unlevered_beta": 1.55, "cash_firm_value_pct": 2.80, "unlevered_beta_cash_adj": 1.59, "hilo_risk": 0.5618, "std_dev_equity_pct": 52.61, "std_dev_op_income_pct": 234.02},
    {"industry": "Software (System & Application)", "num_firms": 309, "levered_beta": 1.28, "de_ratio_pct": 5.58, "tax_rate_pct": 5.51, "unlevered_beta": 1.23, "cash_firm_value_pct": 1.83, "unlevered_beta_cash_adj": 1.25, "hilo_risk": 0.5741, "std_dev_equity_pct": 56.79, "std_dev_op_income_pct": 48.63},
    {"industry": "Steel", "num_firms": 19, "levered_beta": 1.06, "de_ratio_pct": 23.51, "tax_rate_pct": 9.28, "unlevered_beta": 0.90, "cash_firm_value_pct": 4.38, "unlevered_beta_cash_adj": 0.94, "hilo_risk": 0.3648, "std_dev_equity_pct": 38.51, "std_dev_op_income_pct": 85.30},
    {"industry": "Telecom (Wireless)", "num_firms": 12, "levered_beta": 0.54, "de_ratio_pct": 51.95, "tax_rate_pct": 4.02, "unlevered_beta": 0.39, "cash_firm_value_pct": 1.32, "unlevered_beta_cash_adj": 0.39, "hilo_risk": 0.5030, "std_dev_equity_pct": 40.18, "std_dev_op_income_pct": 58.11},
    {"industry": "Telecom. Equipment", "num_firms": 57, "levered_beta": 0.92, "de_ratio_pct": 9.22, "tax_rate_pct": 7.06, "unlevered_beta": 0.86, "cash_firm_value_pct": 2.68, "unlevered_beta_cash_adj": 0.89, "hilo_risk": 0.5619, "std_dev_equity_pct": 55.26, "std_dev_op_income_pct": 11.30},
    {"industry": "Telecom. Services", "num_firms": 39, "levered_beta": 0.63, "de_ratio_pct": 96.06, "tax_rate_pct": 3.40, "unlevered_beta": 0.37, "cash_firm_value_pct": 4.21, "unlevered_beta_cash_adj": 0.38, "hilo_risk": 0.5335, "std_dev_equity_pct": 60.29, "std_dev_op_income_pct": 9.46},
    {"industry": "Tobacco", "num_firms": 10, "levered_beta": 0.79, "de_ratio_pct": 22.97, "tax_rate_pct": 14.77, "unlevered_beta": 0.68, "cash_firm_value_pct": 1.84, "unlevered_beta_cash_adj": 0.69, "hilo_risk": 0.5640, "std_dev_equity_pct": 65.96, "std_dev_op_income_pct": 10.13},
    {"industry": "Transportation", "num_firms": 19, "levered_beta": 0.86, "de_ratio_pct": 36.45, "tax_rate_pct": 8.54, "unlevered_beta": 0.68, "cash_firm_value_pct": 5.09, "unlevered_beta_cash_adj": 0.71, "hilo_risk": 0.4445, "std_dev_equity_pct": 38.13, "std_dev_op_income_pct": 54.77},
    {"industry": "Transportation (Railroads)", "num_firms": 4, "levered_beta": 0.98, "de_ratio_pct": 27.79, "tax_rate_pct": 16.98, "unlevered_beta": 0.81, "cash_firm_value_pct": 0.83, "unlevered_beta_cash_adj": 0.81, "hilo_risk": 0.2393, "std_dev_equity_pct": 23.90, "std_dev_op_income_pct": 13.37},
    {"industry": "Trucking", "num_firms": 26, "levered_beta": 1.01, "de_ratio_pct": 25.23, "tax_rate_pct": 12.60, "unlevered_beta": 0.85, "cash_firm_value_pct": 2.12, "unlevered_beta_cash_adj": 0.87, "hilo_risk": 0.4329, "std_dev_equity_pct": 35.29, "std_dev_op_income_pct": 33.03},
    {"industry": "Utility (General)", "num_firms": 14, "levered_beta": 0.24, "de_ratio_pct": 81.48, "tax_rate_pct": 12.77, "unlevered_beta": 0.15, "cash_firm_value_pct": 0.33, "unlevered_beta_cash_adj": 0.15, "hilo_risk": 0.1301, "std_dev_equity_pct": 14.96, "std_dev_op_income_pct": 13.12},
    {"industry": "Utility (Water)", "num_firms": 14, "levered_beta": 0.41, "de_ratio_pct": 62.36, "tax_rate_pct": 11.19, "unlevered_beta": 0.28, "cash_firm_value_pct": 0.46, "unlevered_beta_cash_adj": 0.28, "hilo_risk": 0.2491, "std_dev_equity_pct": 48.07, "std_dev_op_income_pct": 21.22},
]

betas_output = {
    "source": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html",
    "last_updated_by_damodaran": "January 2026",
    "downloaded": "2026-03-17",
    "total_market_firms": 5994,
    "note": "US data. D/E ratio, tax rate, std dev values are percentages stored as floats (e.g. 40.20 means 40.20%). std_dev_op_income_pct=null means data unavailable (financials).",
    "fields": {
        "industry": "Damodaran industry name",
        "num_firms": "Number of firms in sample",
        "levered_beta": "Levered (equity) beta",
        "de_ratio_pct": "Debt/Equity ratio in percent",
        "tax_rate_pct": "Effective tax rate in percent",
        "unlevered_beta": "Unlevered (asset) beta",
        "cash_firm_value_pct": "Cash as % of firm value",
        "unlevered_beta_cash_adj": "Unlevered beta corrected for cash",
        "hilo_risk": "HiLo risk measure",
        "std_dev_equity_pct": "Standard deviation of equity returns in percent",
        "std_dev_op_income_pct": "Standard deviation of operating income in percent (earnings volatility)"
    },
    "industries": DAMODARAN_RAW
}

out_path = os.path.join(RESEARCH_DIR, "damodaran_betas.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(betas_output, f, indent=2)
print(f"Wrote {out_path} with {len(DAMODARAN_RAW)} industries")

# ──────────────────────────────────────────────────────────────────────────────
# TASK 2: COUNTRY ERP DATA
# ──────────────────────────────────────────────────────────────────────────────

wb = openpyxl.load_workbook(os.path.join(RESEARCH_DIR, "ctryprem.xlsx"), data_only=True)

# Get CDS spreads (columns A,B,C from "10-year CDS Spreads" sheet)
ws_cds = wb["10-year CDS Spreads"]
cds_map = {}
for row in ws_cds.iter_rows(min_row=2, values_only=True):
    country = row[0]
    if country and isinstance(country, str) and not country.startswith("='"):
        cds_raw = row[2]
        if isinstance(cds_raw, (int, float)):
            cds_map[country] = round(float(cds_raw), 6)
        else:
            cds_map[country] = None

# Get ERP data from "ERPs by country" sheet
ws_erp = wb["ERPs by country"]
erp_rows = list(ws_erp.iter_rows(values_only=True))

countries = []
frontier_section = False

for i, row in enumerate(erp_rows):
    if i < 8:
        continue  # skip header rows
    if row[0] is None and row[1] is None:
        continue

    # Detect frontier markets section
    if row[0] == "Frontier Markets (no sovereign ratings)":
        frontier_section = True
        continue
    if frontier_section and row[0] == "Country":
        continue  # skip frontier header row

    country_name = row[0]
    if not country_name or not isinstance(country_name, str):
        continue
    if country_name.startswith("='"):
        continue

    if not frontier_section:
        # Standard: cols: country, region, moody's, rating_default_spread, total_erp, country_risk_premium, cds_net, total_erp2
        region = row[1] if row[1] else None
        moodys = row[2] if row[2] else None
        rating_default_spread = row[3] if isinstance(row[3], (int, float)) else None
        total_erp = row[4] if isinstance(row[4], (int, float)) else None
        country_risk_premium = row[5] if isinstance(row[5], (int, float)) else None
        cds_net = row[6] if isinstance(row[6], (int, float)) else None

        entry = {
            "country": country_name,
            "region": region,
            "moodys_rating": moodys,
            "rating_based_default_spread": round(rating_default_spread, 6) if rating_default_spread is not None else None,
            "equity_risk_premium": round(total_erp, 6) if total_erp is not None else None,
            "country_risk_premium": round(country_risk_premium, 6) if country_risk_premium is not None else None,
            "cds_spread": cds_map.get(country_name),
            "frontier_market": False
        }
    else:
        # Frontier: country, prs_score, erp, crp, default_spread
        prs = row[1] if isinstance(row[1], (int, float)) else None
        erp_v = row[2] if isinstance(row[2], (int, float)) else None
        crp_v = row[3] if isinstance(row[3], (int, float)) else None
        ds_v = row[4] if isinstance(row[4], (int, float)) else None

        entry = {
            "country": country_name,
            "region": None,
            "moodys_rating": "NR",
            "rating_based_default_spread": round(ds_v, 6) if ds_v is not None else None,
            "equity_risk_premium": round(erp_v, 6) if erp_v is not None else None,
            "country_risk_premium": round(crp_v, 6) if crp_v is not None else None,
            "cds_spread": cds_map.get(country_name),
            "frontier_market": True,
            "prs_composite_score": prs
        }

    countries.append(entry)

# Stop at empty rows after frontier
countries = [c for c in countries if c["country"] and c.get("equity_risk_premium") is not None]

erp_output = {
    "source": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx",
    "last_updated_by_damodaran": "January 2026 (sovereign ratings updated Feb 2026)",
    "downloaded": "2026-03-17",
    "mature_market_erp": 0.0423,
    "us_erp": 0.0446,
    "equity_vol_multiplier": 1.5234,
    "note": "ERP values are decimals (e.g. 0.0486 = 4.86%). CDS spreads are also decimals. Countries without Moody's ratings use PRS composite scores.",
    "fields": {
        "country": "Country name",
        "region": "Geographic region",
        "moodys_rating": "Moody's sovereign rating",
        "rating_based_default_spread": "Default spread based on rating (decimal)",
        "equity_risk_premium": "Total equity risk premium = mature market ERP + country risk premium (decimal)",
        "country_risk_premium": "Additional country-specific risk premium above mature market (decimal)",
        "cds_spread": "10-year CDS spread as of 12/31/2025 (decimal, null if unavailable)",
        "frontier_market": "True if country lacks sovereign rating and uses PRS score method",
        "prs_composite_score": "PRS political risk score (frontier markets only, higher = less risk)"
    },
    "countries": countries
}

out_path = os.path.join(RESEARCH_DIR, "country_erp.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(erp_output, f, indent=2)
print(f"Wrote {out_path} with {len(countries)} countries")

# ──────────────────────────────────────────────────────────────────────────────
# TASK 3 & 4: RISK FACTOR SCORES + TICKER-TO-DAMODARAN MAPPING
# ──────────────────────────────────────────────────────────────────────────────

# Helper: compute leverage score from D/E ratio
def de_to_leverage_score(de_pct):
    """D/E ratio (percent) → score 1-10.
    Breakpoints:
    <=5: 1, <=15: 2, <=25: 3, <=35: 4, <=50: 5, <=75: 6, <=100: 7, <=150: 8, <=250: 9, >250: 10
    Financial firms (banks, insurance) with structurally high leverage are handled separately.
    """
    if de_pct is None:
        return 5
    if de_pct <= 5:   return 1
    if de_pct <= 15:  return 2
    if de_pct <= 25:  return 3
    if de_pct <= 35:  return 4
    if de_pct <= 50:  return 5
    if de_pct <= 75:  return 6
    if de_pct <= 100: return 7
    if de_pct <= 150: return 8
    if de_pct <= 250: return 9
    return 10

def earnings_vol_to_score(std_op_pct):
    """Std dev of operating income (percent) → score 1-10.
    Breakpoints:
    None → 5 (neutral)
    <=10: 1, <=15: 2, <=20: 3, <=28: 4, <=38: 5, <=52: 6, <=70: 7, <=100: 8, <=185: 9, >185: 10
    """
    if std_op_pct is None:
        return 5
    if std_op_pct <= 10:  return 1
    if std_op_pct <= 15:  return 2
    if std_op_pct <= 20:  return 3
    if std_op_pct <= 28:  return 4
    if std_op_pct <= 38:  return 5
    if std_op_pct <= 52:  return 6
    if std_op_pct <= 70:  return 7
    if std_op_pct <= 100: return 8
    if std_op_pct <= 185: return 9
    return 10

# Domain knowledge scores for all 10 risk factors per industry
# Format: [int_rate, china_rev, geo_political, currency, regulatory, leverage, earnings_cyc, sector_conc, supply_chain, esg]
# Factors 6 (index 5) and 7 (index 6) will be derived quantitatively below

DOMAIN_SCORES = {
    # industry: [interest_rate, china_revenue, geopolitical, currency, regulatory, leverage_OVERRIDE, earnings_cyc_OVERRIDE, sector_conc, supply_chain, esg]
    # leverage and earnings_cyc set to None = computed from data; int value = override
    "Advertising":                              [6, 3, 4, 6, 5, None, None, 4, 2, 4],
    "Aerospace/Defense":                        [4, 4, 8, 6, 7, None, None, 6, 6, 5],
    "Air Transport":                            [7, 4, 6, 7, 6, None, None, 6, 5, 8],
    "Apparel":                                  [5, 7, 6, 6, 3, None, None, 4, 6, 6],
    "Auto & Truck":                             [6, 7, 6, 6, 5, None, None, 7, 5, 7],
    "Auto Parts":                               [5, 7, 6, 5, 4, None, None, 5, 6, 5],
    "Bank (Money Center)":                      [9, 4, 6, 6, 9, None, None, 8, 1, 4],
    "Banks (Regional)":                         [9, 2, 3, 3, 8, None, None, 7, 1, 3],
    "Beverage (Alcoholic)":                     [4, 5, 4, 5, 5, None, None, 4, 3, 3],
    "Beverage (Soft)":                          [4, 5, 4, 6, 4, None, None, 4, 3, 3],
    "Broadcasting":                             [6, 2, 3, 4, 6, None, None, 5, 2, 3],
    "Brokerage & Investment Banking":           [8, 4, 6, 6, 9, None, None, 7, 1, 4],
    "Building Materials":                       [7, 5, 4, 4, 3, None, None, 4, 4, 5],
    "Business & Consumer Services":             [5, 4, 4, 5, 4, None, None, 4, 2, 3],
    "Cable TV":                                 [7, 2, 3, 3, 6, None, None, 5, 2, 4],
    "Chemical (Basic)":                         [5, 6, 5, 5, 5, None, None, 4, 4, 7],
    "Chemical (Diversified)":                   [5, 5, 5, 5, 5, None, None, 4, 3, 7],
    "Chemical (Specialty)":                     [4, 5, 5, 5, 5, None, None, 4, 3, 6],
    "Coal & Related Energy":                    [5, 4, 5, 4, 7, None, None, 5, 3, 10],
    "Computer Services":                        [4, 5, 4, 5, 4, None, None, 5, 4, 3],
    "Computers/Peripherals":                    [4, 8, 6, 6, 3, None, None, 6, 8, 4],
    "Construction Supplies":                    [7, 5, 4, 4, 3, None, None, 4, 3, 5],
    "Diversified":                              [5, 4, 5, 5, 4, None, None, 3, 3, 4],
    "Drugs (Biotechnology)":                    [3, 5, 4, 6, 7, None, None, 5, 3, 2],
    "Drugs (Pharmaceutical)":                   [3, 5, 4, 7, 8, None, None, 5, 3, 2],
    "Education":                                [4, 4, 3, 4, 6, None, None, 4, 1, 2],
    "Electrical Equipment":                     [4, 7, 5, 6, 4, None, None, 5, 6, 5],
    "Electronics (Consumer & Office)":          [4, 8, 6, 6, 3, None, None, 5, 7, 5],
    "Electronics (General)":                    [4, 7, 5, 6, 3, None, None, 5, 6, 5],
    "Engineering/Construction":                 [6, 6, 6, 5, 5, None, None, 4, 4, 5],
    "Entertainment":                            [4, 5, 4, 6, 4, None, None, 5, 3, 3],
    "Environmental & Waste Services":           [5, 3, 3, 4, 6, None, None, 4, 2, 2],
    "Farming/Agriculture":                      [5, 6, 6, 5, 5, None, None, 3, 5, 6],
    "Financial Svcs. (Non-bank & Insurance)":   [8, 4, 6, 5, 8, None, None, 6, 1, 4],
    "Food Processing":                          [4, 5, 4, 5, 4, None, None, 4, 4, 4],
    "Food Wholesalers":                         [4, 4, 3, 4, 3, None, None, 4, 4, 3],
    "Furn/Home Furnishings":                    [7, 6, 4, 4, 3, None, None, 4, 5, 4],
    "Green & Renewable Energy":                 [7, 4, 4, 4, 7, None, None, 5, 4, 1],
    "Healthcare Products":                      [3, 5, 4, 6, 7, None, None, 5, 4, 2],
    "Healthcare Support Services":              [4, 3, 3, 4, 7, None, None, 5, 2, 2],
    "Healthcare Information and Technology":    [3, 4, 3, 5, 6, None, None, 5, 3, 2],
    "Homebuilding":                             [9, 3, 3, 3, 4, None, None, 6, 4, 5],
    "Hospitals/Healthcare Facilities":          [5, 3, 3, 3, 8, None, None, 5, 2, 2],
    "Hotel/Gaming":                             [6, 6, 6, 7, 5, None, None, 5, 3, 5],
    "Household Products":                       [4, 5, 4, 6, 4, None, None, 4, 4, 4],
    "Information Services":                     [3, 4, 4, 5, 4, None, None, 5, 3, 2],
    "Insurance (General)":                      [7, 3, 4, 5, 7, None, None, 5, 1, 4],
    "Insurance (Life)":                         [9, 3, 4, 5, 7, None, None, 6, 1, 4],
    "Insurance (Prop/Cas.)":                    [7, 3, 4, 5, 7, None, None, 5, 1, 5],
    "Investments & Asset Management":           [7, 5, 5, 6, 7, None, None, 6, 1, 4],
    "Machinery":                                [5, 6, 5, 6, 3, None, None, 4, 5, 5],
    "Metals & Mining":                          [5, 7, 7, 6, 5, None, None, 5, 4, 7],
    "Office Equipment & Services":              [4, 5, 4, 5, 3, None, None, 4, 5, 4],
    "Oil/Gas (Integrated)":                     [4, 5, 8, 6, 6, None, None, 5, 4, 9],
    "Oil/Gas (Production and Exploration)":     [4, 4, 8, 5, 5, None, None, 5, 4, 9],
    "Oil/Gas Distribution":                     [5, 4, 7, 4, 6, None, None, 4, 4, 8],
    "Oilfield Svcs/Equip.":                     [4, 4, 7, 5, 4, None, None, 4, 4, 8],
    "Packaging & Container":                    [5, 5, 4, 4, 3, None, None, 4, 4, 6],
    "Paper/Forest Products":                    [5, 5, 5, 5, 4, None, None, 4, 4, 7],
    "Power":                                    [7, 3, 3, 3, 7, None, None, 5, 3, 6],
    "Precious Metals":                          [4, 5, 7, 5, 4, None, None, 4, 3, 5],
    "Publishing & Newspapers":                  [5, 3, 3, 4, 4, None, None, 4, 2, 3],
    "R.E.I.T.":                                 [9, 2, 2, 2, 5, None, None, 7, 1, 4],
    "Real Estate (Development)":                [8, 5, 5, 4, 5, None, None, 5, 3, 5],
    "Real Estate (General/Diversified)":        [8, 4, 5, 4, 5, None, None, 5, 2, 4],
    "Real Estate (Operations & Services)":      [7, 4, 4, 4, 5, None, None, 4, 2, 4],
    "Recreation":                               [5, 5, 4, 6, 4, None, None, 4, 3, 4],
    "Reinsurance":                              [6, 3, 5, 6, 7, None, None, 4, 1, 4],
    "Restaurant/Dining":                        [5, 4, 4, 5, 4, None, None, 5, 3, 4],
    "Retail (Automotive)":                      [6, 5, 4, 4, 3, None, None, 5, 4, 4],
    "Retail (Building Supply)":                 [7, 4, 3, 4, 3, None, None, 5, 4, 4],
    "Retail (Distributors)":                    [5, 5, 4, 4, 3, None, None, 4, 5, 4],
    "Retail (General)":                         [5, 6, 4, 5, 3, None, None, 5, 5, 4],
    "Retail (Grocery and Food)":                [4, 4, 3, 4, 4, None, None, 5, 4, 4],
    "Retail (REITs)":                           [9, 2, 2, 2, 5, None, None, 7, 1, 4],
    "Retail (Special Lines)":                   [5, 5, 4, 5, 3, None, None, 4, 5, 4],
    "Rubber & Tires":                           [6, 6, 5, 5, 3, None, None, 4, 5, 6],
    "Semiconductor":                            [3, 8, 7, 7, 5, None, None, 7, 10, 5],
    "Semiconductor Equip":                      [3, 8, 7, 7, 5, None, None, 7, 10, 5],
    "Shipbuilding & Marine":                    [5, 6, 6, 6, 4, None, None, 4, 5, 6],
    "Shoe":                                     [5, 7, 5, 6, 3, None, None, 4, 6, 5],
    "Software (Entertainment)":                 [3, 5, 3, 6, 4, None, None, 5, 3, 2],
    "Software (Internet)":                      [3, 6, 4, 7, 5, None, None, 6, 4, 3],
    "Software (System & Application)":          [3, 5, 4, 7, 5, None, None, 6, 4, 2],
    "Steel":                                    [5, 7, 6, 5, 5, None, None, 5, 4, 7],
    "Telecom (Wireless)":                       [7, 4, 4, 5, 7, None, None, 6, 5, 4],
    "Telecom. Equipment":                       [4, 8, 6, 7, 5, None, None, 6, 7, 4],
    "Telecom. Services":                        [7, 4, 5, 5, 8, None, None, 6, 4, 4],
    "Tobacco":                                  [3, 5, 5, 7, 8, None, None, 4, 3, 8],
    "Transportation":                           [5, 5, 6, 6, 4, None, None, 4, 4, 6],
    "Transportation (Railroads)":               [6, 3, 3, 3, 5, None, None, 5, 3, 5],
    "Trucking":                                 [5, 4, 4, 4, 4, None, None, 5, 3, 6],
    "Utility (General)":                        [8, 2, 2, 2, 8, None, None, 5, 3, 6],
    "Utility (Water)":                          [7, 2, 2, 2, 8, None, None, 4, 2, 3],
}

# Build risk factor scores output
factor_names = [
    "interest_rate_risk",
    "china_revenue_risk",
    "geopolitical_country_risk",
    "currency_risk",
    "regulatory_policy_risk",
    "leverage_credit_risk",
    "earnings_cyclicality",
    "sector_concentration_risk",
    "supply_chain_concentration_risk",
    "esg_energy_transition_risk"
]

industry_scores = {}
for row in DAMODARAN_RAW:
    ind = row["industry"]
    domain = DOMAIN_SCORES.get(ind)
    if domain is None:
        print(f"WARNING: no domain scores for {ind}")
        continue

    # Compute quantitative scores
    lev_score = domain[5] if domain[5] is not None else de_to_leverage_score(row["de_ratio_pct"])
    earn_score = domain[6] if domain[6] is not None else earnings_vol_to_score(row["std_dev_op_income_pct"])

    scores = {
        "interest_rate_risk":               domain[0],
        "china_revenue_risk":               domain[1],
        "geopolitical_country_risk":        domain[2],
        "currency_risk":                    domain[3],
        "regulatory_policy_risk":           domain[4],
        "leverage_credit_risk":             lev_score,
        "earnings_cyclicality":             earn_score,
        "sector_concentration_risk":        domain[7],
        "supply_chain_concentration_risk":  domain[8],
        "esg_energy_transition_risk":       domain[9],
    }

    # Validate all scores are 1-10
    for k, v in scores.items():
        assert isinstance(v, int) and 1 <= v <= 10, f"{ind}.{k} = {v} (invalid)"

    industry_scores[ind] = {
        "damodaran_data": {
            "de_ratio_pct": row["de_ratio_pct"],
            "std_dev_op_income_pct": row["std_dev_op_income_pct"],
            "levered_beta": row["levered_beta"],
            "unlevered_beta": row["unlevered_beta"]
        },
        "risk_scores": scores,
        "composite_risk_score": round(sum(scores.values()) / 10, 2)
    }

# ──────────────────────────────────────────────────────────────────────────────
# TASK 4: TICKER-TO-DAMODARAN MAPPING
# ──────────────────────────────────────────────────────────────────────────────

# yfinance uses GICS-based sector/industry strings
# Maps: (yfinance_sector, yfinance_industry) → damodaran_industry
# yfinance sector values: Technology, Healthcare, Financials, Consumer Discretionary,
#   Consumer Staples, Energy, Materials, Industrials, Real Estate, Utilities,
#   Communication Services

YFINANCE_TO_DAMODARAN = {
    # ── Technology ──
    ("Technology", "Semiconductors"):                           "Semiconductor",
    ("Technology", "Semiconductor Equipment & Materials"):      "Semiconductor Equip",
    ("Technology", "Software—Application"):                     "Software (System & Application)",
    ("Technology", "Software—Infrastructure"):                  "Software (System & Application)",
    ("Technology", "Information Technology Services"):          "Computer Services",
    ("Technology", "Computer Hardware"):                        "Computers/Peripherals",
    ("Technology", "Electronic Components"):                    "Electronics (General)",
    ("Technology", "Consumer Electronics"):                     "Electronics (Consumer & Office)",
    ("Technology", "Scientific & Technical Instruments"):       "Electrical Equipment",
    ("Technology", "Solar"):                                    "Green & Renewable Energy",
    ("Technology", "Communication Equipment"):                  "Telecom. Equipment",
    ("Technology", "Electronic Gaming & Multimedia"):           "Software (Entertainment)",
    ("Technology", "Internet Content & Information"):           "Software (Internet)",
    ("Technology", "Data Storage"):                             "Computers/Peripherals",

    # ── Communication Services ──
    ("Communication Services", "Internet Content & Information"):    "Software (Internet)",
    ("Communication Services", "Telecom Services"):                  "Telecom. Services",
    ("Communication Services", "Wireless Telecom Services"):         "Telecom (Wireless)",
    ("Communication Services", "Telecom Equipment"):                 "Telecom. Equipment",
    ("Communication Services", "Broadcasting"):                      "Broadcasting",
    ("Communication Services", "Entertainment"):                     "Entertainment",
    ("Communication Services", "Electronic Gaming & Multimedia"):    "Software (Entertainment)",
    ("Communication Services", "Publishing"):                        "Publishing & Newspapers",
    ("Communication Services", "Advertising Agencies"):              "Advertising",

    # ── Healthcare ──
    ("Healthcare", "Biotechnology"):                                "Drugs (Biotechnology)",
    ("Healthcare", "Drug Manufacturers—General"):                   "Drugs (Pharmaceutical)",
    ("Healthcare", "Drug Manufacturers—Specialty & Generic"):       "Drugs (Pharmaceutical)",
    ("Healthcare", "Medical Devices"):                              "Healthcare Products",
    ("Healthcare", "Medical Instruments & Supplies"):               "Healthcare Products",
    ("Healthcare", "Health Information Services"):                  "Healthcare Information and Technology",
    ("Healthcare", "Healthcare Plans"):                             "Healthcare Support Services",
    ("Healthcare", "Medical Care Facilities"):                      "Hospitals/Healthcare Facilities",
    ("Healthcare", "Diagnostics & Research"):                       "Healthcare Products",
    ("Healthcare", "Pharmaceutical Retailers"):                     "Drugs (Pharmaceutical)",
    ("Healthcare", "Medical Distribution"):                         "Healthcare Support Services",

    # ── Financials ──
    ("Financial Services", "Banks—Diversified"):                    "Bank (Money Center)",
    ("Financial Services", "Banks—Regional"):                       "Banks (Regional)",
    ("Financial Services", "Insurance—Life"):                       "Insurance (Life)",
    ("Financial Services", "Insurance—Property & Casualty"):        "Insurance (Prop/Cas.)",
    ("Financial Services", "Insurance—Diversified"):                "Insurance (General)",
    ("Financial Services", "Insurance—Specialty"):                  "Insurance (General)",
    ("Financial Services", "Insurance—Reinsurance"):                "Reinsurance",
    ("Financial Services", "Capital Markets"):                      "Brokerage & Investment Banking",
    ("Financial Services", "Asset Management"):                     "Investments & Asset Management",
    ("Financial Services", "Financial Data & Stock Exchanges"):     "Information Services",
    ("Financial Services", "Credit Services"):                      "Financial Svcs. (Non-bank & Insurance)",
    ("Financial Services", "Mortgage Finance"):                     "Financial Svcs. (Non-bank & Insurance)",
    ("Financial Services", "Financial Conglomerates"):              "Diversified",
    # yfinance sometimes uses "Financials" as sector
    ("Financials", "Banks—Diversified"):                            "Bank (Money Center)",
    ("Financials", "Banks—Regional"):                               "Banks (Regional)",
    ("Financials", "Capital Markets"):                              "Brokerage & Investment Banking",
    ("Financials", "Asset Management"):                             "Investments & Asset Management",

    # ── Consumer Discretionary ──
    ("Consumer Cyclical", "Auto Manufacturers"):                    "Auto & Truck",
    ("Consumer Cyclical", "Auto Parts"):                            "Auto Parts",
    ("Consumer Cyclical", "Apparel Retail"):                        "Apparel",
    ("Consumer Cyclical", "Apparel Manufacturing"):                 "Apparel",
    ("Consumer Cyclical", "Footwear & Accessories"):                "Shoe",
    ("Consumer Cyclical", "Home Improvement Retail"):               "Retail (Building Supply)",
    ("Consumer Cyclical", "Specialty Retail"):                      "Retail (Special Lines)",
    ("Consumer Cyclical", "Department Stores"):                     "Retail (General)",
    ("Consumer Cyclical", "Discount Stores"):                       "Retail (General)",
    ("Consumer Cyclical", "Auto & Truck Dealerships"):              "Retail (Automotive)",
    ("Consumer Cyclical", "Restaurants"):                           "Restaurant/Dining",
    ("Consumer Cyclical", "Lodging"):                               "Hotel/Gaming",
    ("Consumer Cyclical", "Gambling"):                              "Hotel/Gaming",
    ("Consumer Cyclical", "Resorts & Casinos"):                     "Hotel/Gaming",
    ("Consumer Cyclical", "Leisure"):                               "Recreation",
    ("Consumer Cyclical", "Home Furnishings & Fixtures"):           "Furn/Home Furnishings",
    ("Consumer Cyclical", "Furnishings, Fixtures & Appliances"):    "Furn/Home Furnishings",
    ("Consumer Cyclical", "Personal Services"):                     "Business & Consumer Services",
    ("Consumer Cyclical", "Travel Services"):                       "Recreation",
    ("Consumer Cyclical", "Internet Retail"):                       "Retail (Special Lines)",
    ("Consumer Cyclical", "Publishing"):                            "Publishing & Newspapers",
    ("Consumer Discretionary", "Auto Manufacturers"):               "Auto & Truck",
    ("Consumer Discretionary", "Auto Parts"):                       "Auto Parts",
    ("Consumer Discretionary", "Specialty Retail"):                 "Retail (Special Lines)",
    ("Consumer Discretionary", "Restaurants"):                      "Restaurant/Dining",
    ("Consumer Discretionary", "Leisure"):                          "Recreation",

    # ── Consumer Staples ──
    ("Consumer Defensive", "Beverages—Non-Alcoholic"):              "Beverage (Soft)",
    ("Consumer Defensive", "Beverages—Alcoholic"):                  "Beverage (Alcoholic)",
    ("Consumer Defensive", "Beverages—Brewers"):                    "Beverage (Alcoholic)",
    ("Consumer Defensive", "Beverages—Wineries & Distilleries"):    "Beverage (Alcoholic)",
    ("Consumer Defensive", "Grocery Stores"):                       "Retail (Grocery and Food)",
    ("Consumer Defensive", "Food Distribution"):                    "Food Wholesalers",
    ("Consumer Defensive", "Packaged Foods"):                       "Food Processing",
    ("Consumer Defensive", "Tobacco"):                              "Tobacco",
    ("Consumer Defensive", "Household & Personal Products"):        "Household Products",
    ("Consumer Defensive", "Drug Stores"):                          "Retail (Special Lines)",
    ("Consumer Defensive", "Education & Training Services"):        "Education",
    ("Consumer Staples", "Beverages—Non-Alcoholic"):                "Beverage (Soft)",
    ("Consumer Staples", "Packaged Foods"):                         "Food Processing",
    ("Consumer Staples", "Tobacco"):                                "Tobacco",
    ("Consumer Staples", "Household & Personal Products"):          "Household Products",

    # ── Energy ──
    ("Energy", "Oil & Gas Integrated"):                             "Oil/Gas (Integrated)",
    ("Energy", "Oil & Gas E&P"):                                    "Oil/Gas (Production and Exploration)",
    ("Energy", "Oil & Gas Drilling"):                               "Oilfield Svcs/Equip.",
    ("Energy", "Oil & Gas Equipment & Services"):                   "Oilfield Svcs/Equip.",
    ("Energy", "Oil & Gas Midstream"):                              "Oil/Gas Distribution",
    ("Energy", "Oil & Gas Refining & Marketing"):                   "Oil/Gas Distribution",
    ("Energy", "Coal"):                                             "Coal & Related Energy",
    ("Energy", "Uranium"):                                          "Metals & Mining",
    ("Energy", "Renewable Utilities"):                              "Green & Renewable Energy",

    # ── Materials ──
    ("Basic Materials", "Steel"):                                   "Steel",
    ("Basic Materials", "Aluminum"):                                "Metals & Mining",
    ("Basic Materials", "Copper"):                                  "Metals & Mining",
    ("Basic Materials", "Other Industrial Metals & Mining"):        "Metals & Mining",
    ("Basic Materials", "Gold"):                                    "Precious Metals",
    ("Basic Materials", "Silver"):                                   "Precious Metals",
    ("Basic Materials", "Specialty Chemicals"):                     "Chemical (Specialty)",
    ("Basic Materials", "Chemicals"):                               "Chemical (Basic)",
    ("Basic Materials", "Agricultural Inputs"):                     "Chemical (Specialty)",
    ("Basic Materials", "Paper & Paper Products"):                  "Paper/Forest Products",
    ("Basic Materials", "Packaging & Containers"):                  "Packaging & Container",
    ("Basic Materials", "Building Materials"):                      "Building Materials",
    ("Basic Materials", "Lumber & Wood Production"):                "Paper/Forest Products",
    ("Materials", "Steel"):                                         "Steel",
    ("Materials", "Gold"):                                          "Precious Metals",
    ("Materials", "Chemicals"):                                     "Chemical (Basic)",

    # ── Industrials ──
    ("Industrials", "Aerospace & Defense"):                         "Aerospace/Defense",
    ("Industrials", "Airlines"):                                    "Air Transport",
    ("Industrials", "Railroads"):                                   "Transportation (Railroads)",
    ("Industrials", "Trucking"):                                    "Trucking",
    ("Industrials", "Marine Shipping"):                             "Shipbuilding & Marine",
    ("Industrials", "Integrated Freight & Logistics"):              "Transportation",
    ("Industrials", "Air Freight & Logistics"):                     "Transportation",
    ("Industrials", "Farm & Heavy Construction Machinery"):         "Machinery",
    ("Industrials", "Industrial Machinery"):                        "Machinery",
    ("Industrials", "Specialty Industrial Machinery"):              "Machinery",
    ("Industrials", "Electrical Equipment & Parts"):                "Electrical Equipment",
    ("Industrials", "Engineering & Construction"):                  "Engineering/Construction",
    ("Industrials", "Building Products & Equipment"):               "Building Materials",
    ("Industrials", "Waste Management"):                            "Environmental & Waste Services",
    ("Industrials", "Pollution & Treatment Controls"):              "Environmental & Waste Services",
    ("Industrials", "Business Services"):                           "Business & Consumer Services",
    ("Industrials", "Staffing & Employment Services"):              "Business & Consumer Services",
    ("Industrials", "Security & Protection Services"):              "Business & Consumer Services",
    ("Industrials", "Tools & Accessories"):                         "Machinery",
    ("Industrials", "Rental & Leasing Services"):                   "Business & Consumer Services",
    ("Industrials", "Conglomerates"):                               "Diversified",
    ("Industrials", "Consulting Services"):                         "Business & Consumer Services",
    ("Industrials", "Research & Consulting Services"):              "Business & Consumer Services",

    # ── Real Estate ──
    ("Real Estate", "REIT—Retail"):                                 "Retail (REITs)",
    ("Real Estate", "REIT—Office"):                                 "R.E.I.T.",
    ("Real Estate", "REIT—Industrial"):                             "R.E.I.T.",
    ("Real Estate", "REIT—Residential"):                            "R.E.I.T.",
    ("Real Estate", "REIT—Healthcare Facilities"):                  "R.E.I.T.",
    ("Real Estate", "REIT—Hotel & Motel"):                          "R.E.I.T.",
    ("Real Estate", "REIT—Diversified"):                            "R.E.I.T.",
    ("Real Estate", "REIT—Specialty"):                              "R.E.I.T.",
    ("Real Estate", "REIT—Mortgage"):                               "Financial Svcs. (Non-bank & Insurance)",
    ("Real Estate", "Real Estate—Development"):                     "Real Estate (Development)",
    ("Real Estate", "Real Estate—Diversified"):                     "Real Estate (General/Diversified)",
    ("Real Estate", "Real Estate Services"):                        "Real Estate (Operations & Services)",

    # ── Utilities ──
    ("Utilities", "Utilities—Regulated Electric"):                  "Utility (General)",
    ("Utilities", "Utilities—Regulated Gas"):                       "Utility (General)",
    ("Utilities", "Utilities—Regulated Water"):                     "Utility (Water)",
    ("Utilities", "Utilities—Diversified"):                         "Utility (General)",
    ("Utilities", "Utilities—Independent Power Producers"):         "Power",
    ("Utilities", "Utilities—Renewable"):                           "Green & Renewable Energy",
}

# Also provide sector-only fallback mapping (when industry not matched)
SECTOR_FALLBACK = {
    "Technology":               "Software (System & Application)",
    "Communication Services":   "Telecom. Services",
    "Healthcare":               "Healthcare Products",
    "Financial Services":       "Investments & Asset Management",
    "Financials":               "Investments & Asset Management",
    "Consumer Cyclical":        "Retail (Special Lines)",
    "Consumer Discretionary":   "Retail (Special Lines)",
    "Consumer Defensive":       "Food Processing",
    "Consumer Staples":         "Food Processing",
    "Energy":                   "Oil/Gas (Production and Exploration)",
    "Basic Materials":          "Chemical (Specialty)",
    "Materials":                "Chemical (Specialty)",
    "Industrials":              "Machinery",
    "Real Estate":              "R.E.I.T.",
    "Utilities":                "Utility (General)",
}

# Convert mapping keys to lists for JSON serialization
yf_mapping_serializable = {}
for (sector, industry), damod in YFINANCE_TO_DAMODARAN.items():
    key = f"{sector}|{industry}"
    yf_mapping_serializable[key] = damod

risk_scores_output = {
    "schema_version": "1.0",
    "last_updated": "2026-03-17",
    "data_source": "Damodaran (January 2026), domain knowledge assignments",
    "scoring_rubric": {
        "scale": "1-10 (integer), 1=lowest risk, 10=highest risk",
        "leverage_credit_risk": "Derived quantitatively from Damodaran D/E ratio. Breakpoints: <=5%->1, <=15%->2, <=25%->3, <=35%->4, <=50%->5, <=75%->6, <=100%->7, <=150%->8, <=250%->9, >250%->10",
        "earnings_cyclicality": "Derived quantitatively from Damodaran std dev of operating income. Breakpoints: <=10%->1, <=15%->2, <=20%->3, <=28%->4, <=38%->5, <=52%->6, <=70%->7, <=100%->8, <=185%->9, >185%->10. null std_dev uses neutral score 5.",
        "interest_rate_risk": "Duration sensitivity proxy. Long-duration assets (utilities, REITs, life insurance) score 7-9. Growth sectors with near-term cash flows score 2-4.",
        "china_revenue_risk": "Estimated % revenue exposure to China by sector. Semiconductors, electronics, autos highest (7-9). Domestic services lowest (1-3).",
        "geopolitical_country_risk": "EM/frontier market revenue exposure, defense contracts, commodity extraction in unstable regions.",
        "currency_risk": "% foreign revenue. Global multinationals, commodities, tech with global sales score 6-8. Domestic utilities/banks score 1-3.",
        "regulatory_policy_risk": "Government intervention sensitivity. Healthcare, financials, utilities, telecom score 6-9. Industrial manufacturing scores 3-5.",
        "sector_concentration_risk": "Tendency of sector to be highly concentrated (few dominant players) in GICS indexes. Semiconductors, banks, REITs score 6-8.",
        "supply_chain_concentration_risk": "Dependency on Taiwan/TSMC/semiconductor inputs. Semis score 10. Pure software/services score 1-2.",
        "esg_energy_transition_risk": "Fossil fuel intensity, carbon emissions, stranded asset risk. Coal=10, oil=9, utilities=5-6, software=2."
    },
    "risk_factors": {
        "1_interest_rate_risk": "Interest rate sensitivity via P/E duration proxy and sector leverage to 10Y treasury moves",
        "2_china_revenue_risk": "Estimated revenue exposure to China by sector/industry",
        "3_geopolitical_country_risk": "Exposure to emerging/frontier markets, geopolitical instability",
        "4_currency_risk": "Foreign revenue exposure and currency translation risk",
        "5_regulatory_policy_risk": "Government intervention, regulation changes, and policy risk",
        "6_leverage_credit_risk": "Quantitative: derived from D/E ratio in Damodaran data",
        "7_earnings_cyclicality": "Quantitative: derived from std dev of operating income in Damodaran data",
        "8_sector_concentration_risk": "GICS index overlap tendency, market concentration",
        "9_supply_chain_concentration_risk": "Taiwan/TSMC/semiconductor supply chain dependency",
        "10_esg_energy_transition_risk": "Fossil fuel intensity, carbon risk, energy transition exposure"
    },
    "industries": industry_scores,
    "yfinance_to_damodaran_mapping": {
        "description": "Maps (yfinance_sector, yfinance_industry) tuples to Damodaran industry names. Key format: 'sector|industry'.",
        "usage": "Look up ticker sector+industry from yfinance info dict, then concatenate with '|' to find Damodaran industry. Fall back to sector_only if not found.",
        "exact_mapping": yf_mapping_serializable,
        "sector_only_fallback": SECTOR_FALLBACK
    }
}

out_path = os.path.join(RESEARCH_DIR, "risk_factor_scores.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(risk_scores_output, f, indent=2)
print(f"Wrote {out_path} with {len(industry_scores)} industries")

# ──────────────────────────────────────────────────────────────────────────────
# TASK 5: DATA SOURCES
# ──────────────────────────────────────────────────────────────────────────────

data_sources = {
    "ctryprem": {
        "source": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx",
        "last_updated_by_damodaran": "January 2026",
        "downloaded": "2026-03-17",
        "note": "Country default spreads and risk premiums based on Moody's ratings and CDS spreads"
    },
    "betas": {
        "source": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html",
        "last_updated_by_damodaran": "January 2026",
        "downloaded": "2026-03-17",
        "note": "Industry betas, D/E ratios, and unlevered betas for ~100 industries"
    }
}

out_path = os.path.join(RESEARCH_DIR, "data_sources.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data_sources, f, indent=2)
print(f"Wrote {out_path}")

print("\nAll JSON files written successfully.")
