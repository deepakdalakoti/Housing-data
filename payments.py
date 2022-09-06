import numpy as np

class Mortgage():
    def __init__(self, interest, years, property_price, deposit, other_expenses):
        #monthly interest
        #interest in num
        self.interest = interest/(12*100)
        self.years = years
        self.months = self.years*12
        self.principal = property_price + other_expenses - deposit
        self.property_price = property_price
        self.deposit = deposit
        self.other_expenses = other_expenses

    def get_monthly_payments(self):
        return np.ceil(self.interest*self.principal/(1-(1+self.interest)**(-self.months)))

    def get_total_interest_paid(self, years, extra_payments=0):
        monthly_payments = self.get_monthly_payments() + extra_payments
        periods = years*12
        return (self.principal*self.interest-monthly_payments)*((1+self.interest)**periods-1)/self.interest + monthly_payments*periods

    def get_principal_remaining(self, years, extra_payments=0):
        interest = self.get_total_interest_paid(years, extra_payments)
        total_paid = (self.get_monthly_payments()+extra_payments)*years*12
        return self.principal - (total_paid-interest)

    def get_principal_paid(self, years, extra_payments=0):
        return self.principal - self.get_principal_remaining(years,extra_payments)

    def get_stats_current_val(self, years, inflation, extra_payments=0):
        monthly  = self.get_monthly_payments() + extra_payments
        princ = self.principal
        current_interest = 0
        current_principal = 0
        #montly interest rate
        rate = inflation/1200
        total_princ = 0
        for i in range(years*12):
            interest = princ*self.interest
            princ = princ - (monthly-interest)
            total_princ = total_princ + (monthly-interest)
            current_interest = current_interest + interest/(1+rate)**i
            current_principal = current_principal+(monthly-interest)/(1+rate)**i
        return current_principal, current_interest

    @staticmethod
    def do_compounding(principal, years, interest):
       #compounding yearly
       return principal*(1+interest/100)**years

    def pl_report(self, years_hold, growth_rate, inflation, extra_payments, rent=0, index_rate=6):
       sold_price = self.do_compounding(self.property_price, years_hold, growth_rate)
       monthly = self.get_monthly_payments()
       interest_paid = self.get_total_interest_paid(years_hold, extra_payments)
       principal_paid = self.get_principal_paid(years_hold, extra_payments)
       total_paid = principal_paid  + self.deposit 
       sold_gain = (sold_price-(self.principal-principal_paid))
       owning_cost = total_paid + interest_paid + self.other_expenses
       money_left = sold_gain - owning_cost
       curr_val = money_left/(1+growth_rate/100)**years_hold
       current_principal, current_interest = self.get_stats_current_val(years_hold, inflation, extra_payments)
       cur_sale = sold_price/(1+inflation/100)**years_hold
       current_own_cost = current_principal+current_interest+self.other_expenses
       cur_sold_gain = sold_gain/(1+inflation/100)**years_hold
       current_profit = cur_sold_gain-current_own_cost
       inflation_month = inflation/1200
       rent_current = rent*4*(1-(1+inflation_month)**(-years_hold*12))/inflation_month
       spare_cash_if_no_buy = monthly+extra_payments - rent*4
       #if invested in an index fund what will be the value in years_hold
       spare_val = spare_cash_if_no_buy*((1+index_rate/1200)**(12*years_hold)-1)*1200/index_rate
       #what is the current value of this considering inflation
       cur_val_spare = spare_val/(1+inflation/100)**years_hold
       out_str = f'''Property price: AUD {self.property_price} \n
                     Loan after deposit and costs: AUD {self.principal} \n
                     LVR: {self.principal/self.property_price} \n
                     Minimum monthly repayments: AUD {monthly} \n
                     Extra payments: AUD {extra_payments} \n
                     Total monthly payments AUD: {monthly+extra_payments} \n
                     Held the property for {years_hold} years \n
                     Property price in {years_hold} years with {growth_rate} percent compounding will be AUD {sold_price} \n
                     Total interest paid: AUD {interest_paid} \n
                     Principal paid: AUD {principal_paid} \n
                     Profit from selling after settling with bank: AUD {sold_gain} \n
                     Total cost of owning: {owning_cost} \n
                     Profit: {money_left} \n
                     Current value of profit if {inflation}% discounting applied: AUD {curr_val} \n
                     Current value of principal: AUD {current_principal} \n
                     Current value of interest: AUD {current_interest} \n
                     Current value of sold price: AUD {cur_sale} \n
                     Profit based on current value: AUD {current_profit} \n
                     Total money: principal + profit: AUD {current_principal+current_profit} \n
                     If instead invested money left after rent in index fund, current val: AUD {cur_val_spare} \n
       '''
       return out_str.split('\n')

    def get_rent_expenditure(self,weekly, rate, years):
        annual_payment = weekly*52
        present_val = annual_payment*(1-(1+rate/100)**(-years))*100/rate
        return present_val
