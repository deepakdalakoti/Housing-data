import math
import sys
from functools import lru_cache
import numpy as np

class Mortgage:
    def __init__(self, interest, loan, years, interest_only=False):
        # Monthly interest
        self.interest = interest / (12 * 100)
        self.loan = loan
        self.years = years
        self.months = self.years * 12
        self.interest_only = interest_only

    def get_monthly_payments(self):
        if self.interest_only:
            return self.get_monthly_interest_only_payment()

        return np.ceil(
            self.interest * self.loan / (1 - (1 + self.interest) ** (-self.months))
        )

    def get_monthly_interest_only_payment(self):
        return np.ceil(self.interest * self.loan)

    def get_total_interest_paid(self, years, extra_payments=0):
        monthly_payments = self.get_monthly_payments() + extra_payments
        periods = years * 12
        return (self.loan * self.interest - monthly_payments) * (
            (1 + self.interest) ** periods - 1
        ) / self.interest + monthly_payments * periods

    def get_principal_remaining(self, years, extra_payments=0):
        interest = self.get_total_interest_paid(years, extra_payments)
        total_paid = (self.get_monthly_payments() + extra_payments) * years * 12
        return self.loan - (total_paid - interest)

    def get_principal_paid(self, years, extra_payments=0):
        return self.loan - self.get_principal_remaining(years, extra_payments)

class Property(Mortgage):
    """Year = 1 means position after owning property for one year"""
    def __init__(
        self,
        price,
        deposit,
        buying_cost,
        growth_rate,
        interest_rate,
        rent=0,
        extra_repayments=0,
        cost_growth_rate=0,
        running_cost=0,
        lmi=0,
        strategy="ppor",
        owner_occupied_years=None,
    ):
        super().__init__(
            interest_rate,
            price - deposit + buying_cost + lmi,
            years=30,
            interest_only=True if strategy=='rentvest' else False,
        )
        self.price = price
        self.deposit = deposit
        self.buying_cost = buying_cost
        self.growth_rate = growth_rate
        self.extra_repayments = extra_repayments

        self.rent = rent
        self.running_cost = running_cost
        self.lmi = lmi
        self.strategy = strategy
        self.owner_occupied_years = owner_occupied_years
        # Growth rate in costs and rent recevied
        # TODO -> have different growth rate for each
        # monthly
        self.cost_growth_rate = cost_growth_rate / 1200
        min_repayment = self.get_monthly_payments()
        if(self.strategy=='rentvest'):
            if self.rent + self.running_cost - min_repayment < 0:
                print(
                  "Running cost higher than rental income earned, property negatively geared"
                )
            else:
                print("Property positively geared")
        
        self.sanity_check()

    def sanity_check(self):
        """Sanity check on input parameters"""
        if(self.strategy=='ppor'):
            assert self.rent == 0, "PPOR should not have rent"
            assert not self.interest_only, "PPOR should not be interest only"

        if(self.strategy=='rentvest'):
            assert self.rent > 0, "Rentvest should have rent"

        if(self.strategy=='convert_to_rent'):
            assert self.rent > 0, "Convert to rent should have rent"
            assert self.owner_occupied_years > 0, "Convert to rent should have owner occupied years"
        
        assert self.deposit > self.buying_cost, "Deposit should be more than buying cost"
        assert self.rent >=0, "Rent should be positive"
        assert self.strategy in ['ppor','rentvest','convert_to_rent'], "Strategy should be either ppor or rentvest"
        if(self.strategy == 'convert_to_rent'):
            assert self.owner_occupied_years >=0, "Owner occupied years should be positive"

    def get_property_position(self, years, months=0):
        if(self.strategy=="convert_to_rent"):
            #If property is to be converted to rent for first few years it will be normal property with 0 rent
            years_ppor = min(years, self.owner_occupied_years)
            loan_left, offset, oop = self.get_property_position_calc(years_ppor, self.get_monthly_payments(), 0, self.running_cost, self.loan, months)
            #After that it will be rentvest property
            years_rentvest = max(years - years_ppor,0)
            loan_left, offset_1, oop_1 = self.get_property_position_calc(years_rentvest, self.get_monthly_interest_only_payment(), self.rent, self.running_cost, loan_left, months)
            return loan_left, offset + offset_1, oop + oop_1

        else:
            return self.get_property_position_calc(years, self.get_monthly_payments(), self.rent, self.running_cost, self.loan, months)


    #@lru_cache(maxsize=32)
    def get_property_position_calc(self, years, min_repayment, rent, running_cost, loan, months=0):
        """If we reinvest/put in offset whatever money we earn from rent what happens then
        Interest will change every period, use brute force method to compute

        """

        out_of_pocket=0
        offset=0
        loan_left = loan
        #min_repayment = self.get_monthly_payments()
        periods = years*12 + months
        for _ in range(0, periods):
            
            earning = rent
            #interest is not charged on any money in offset account
            interest_repayment = self.interest * (loan_left-offset)

            principal_repayments = min_repayment - interest_repayment
            #Loan left is only for interest calculation purposes, loan is not actually decreasing, money is going to offset
            loan_left = loan_left - principal_repayments
            #If earnings + extra repayments is more than min repayments then I am paying extra, otherwise coming out of pocket
            extra_repayments = earning + self.extra_repayments - min_repayment - running_cost*(1+self.cost_growth_rate)
            out_of_pocket = out_of_pocket + min(0, extra_repayments)
            #If any extra money is left, it will go to offset account
            offset = offset + max(0,extra_repayments)

        return loan_left, offset, abs(out_of_pocket)


    def get_property_val(self, years):
        """Property value compounding"""
        return self.do_compounding(self.price, years, self.growth_rate)

    def get_monthly_oop_payments(self):
        """How much per month needs to be paid after accounting for rent"""
        min_payment = self.get_monthly_payments()
        return min(min_payment - self.rent - self.running_cost,0)

    def get_principal_paid(self, years, extra_payments=0):
        """How much principal has been paid in years"""
        if self.strategy == "ppor":
            return super().get_principal_paid(years, extra_payments)
        elif self.strategy in ["rentvest","convert_to_rent"]:
            loan_left, _, _ = self.get_property_position(years)
            return self.loan - loan_left
        else:
            print(f"Strategy {self.strategy} not implemented")
            return 0

    def get_interest_paid(self, years):
        """How much interest has been paid in years"""
        if self.strategy in ["ppor", "rentvest"]:
            return super().get_total_interest_paid(years, self.extra_repayments)
        else:
            print(f"Strategy {self.strategy} not implemented")
            return 0

    def total_equity_at_year(self, years, factor=1.0):
        """How much equity has been created? Equity = property value + principal paid - loan
        Equity is proerty value minus loan left"""
        property_value = self.get_property_val(years)
        principal_paid = self.get_principal_paid(years)
        equity = factor*property_value + principal_paid - self.loan
        return equity

    def get_running_costs(self, years):
        _, _, oop = self.get_property_position(years)
        return oop
    
    def get_net_cash_flow(self, years):
        """Net cash flow for this property, negative means cash out, positive means cash in"""
        _, offset, oop = self.get_property_position(years)
        return offset - oop
    
    def get_net_cash_flow_at_year(self, years):
        """Net cash flow for this property, negative means cash out, positive means cash in"""
        if(years<=0):
            return 0
        
        _, offset_1, oop_1 = self.get_property_position(years-1)
        _, offset, oop = self.get_property_position(years)
        return (offset - oop) - (offset_1 - oop_1)
    
    def net_position_at_year(self, years):
        """Net wealth position in years
        Calculated as:
        equity - deposit - running cost - interest paid
        """
        loan_left, _, oop = self.get_property_position(years)
        net_position = self.get_property_val(years) - loan_left - self.deposit - oop
 
        return net_position

    def get_avg_return_at_year(self, years):
        """What's the profit generated from investment?
        What is the net yearly return on investment?
        """
        net_position = self.net_position_at_year(years)
        total_owning_cost = -1.0*self.get_net_cash_flow(years) + self.deposit
        #Average yearly return?
        avg_return = (net_position/total_owning_cost*100)/years
        return avg_return

    def get_lvr_at_year(self, years):
        """LVR considering payments and property growth"""
        loan_left = self.get_property_position(years)[0]
        property_val = self.get_property_val(years)
        return loan_left/property_val

    @staticmethod
    def do_compounding(principal, years, interest):
        """Simple compounding"""
        return principal * (1 + interest / 100) ** years

class Portfolio:
    """Class for portfolio of property which tracks performance"""

    def __init__(
        self,
        properties: list[Property],
        buy_year: list[float],
        equity_use_fraction: list[float], #what fraction of deposit for a property comes from equity, rest comes from cash
        cash: float,
        monthly_income: float,
        monthly_living_expenses: float,
        monthly_living_rent: float,
        income_growth_rate: float = 0,
        expenses_growth_rate: float = 0
    ):
        self.properties = properties
        self.buy_year = buy_year
        self.equity_use_fraction = equity_use_fraction
        self.cash = cash
        self.monthly_income = monthly_income
        self.income_growth_rate = income_growth_rate
        self.expenses_growth_rate = expenses_growth_rate
        self.monthly_living_expenses = monthly_living_expenses
        self.monthly_living_rent = monthly_living_rent
        self.has_ppor = "ppor" in [prop.strategy for prop in self.properties]

        self.monthly_savings = self.monthly_income - self.monthly_living_expenses

        self.sanity_check()
        
    def sanity_check(self):
        #assert self.deposits <= self.cash, "Not enough cash to buy this portfolio of properties"
        assert len(self.buy_year) == len(self.properties), "Buy year must be specified for each property"
        assert len(self.equity_use_fraction) == len(self.properties), "Equity use fraction must be specified for each property"
        if not self.has_ppor:
            assert self.monthly_living_rent > 0, "Rent cannot be 0 if no ppor proerty in portfolio"
        assert len([prop for prop in self.properties if prop.strategy == "ppor"]) <= 1, "Only one ppor property allowed"
        assert len([prop for prop in self.properties if prop.strategy == "convert_to_rent"]) <= 1, "Only one convert_to_rent property allowed"

    def validate_portfolio(self):
        """Check if portfolio is valid"""
        # Check if enough cash to run properties
        # Check if enough cash to live
        #TODO -> account for rent
        max_year = max(self.buy_year)+1
        cash_flow = self.get_cash_flow(max_year)
        income = Property.do_compounding(self.monthly_income*12, max_year, self.income_growth_rate)
        expenses = Property.do_compounding(self.monthly_living_expenses*12, max_year, self.expenses_growth_rate)
        net_cash = income -  expenses - cash_flow
        if(net_cash<0):
            print("Property portfolio unsustaninable")
        print(f"Savings to property cash_flow: {(income-expenses)/cash_flow*100:.2f}%")
        return
       

    def get_cash_flow(self, years):
        """Cash flow for the portfolio"""
        # What is the cash flow for each property

        property_cash_flow = [prop.get_net_cash_flow(years-self.buy_year[i]) if self.buy_year[i] < years else 0 for i, prop in enumerate(self.properties)]
        return sum(property_cash_flow)
    
    def get_equity_at_year(self, years, factor=1.0):
        """Equity in the portfolio"""
        # What is the equity for each property
        property_equity = [prop.total_equity_at_year(years-self.buy_year[i], factor=factor) if self.buy_year[i] <= years else 0 for i, prop in enumerate(self.properties)]
        return sum(property_equity) - self.get_equity_deposit_paid_at_year(years)

    def get_deposit_needed_at_year(self, years):
        #How much deposit is needed to buy properties?
        deposit = 0
        for i, year in enumerate(self.buy_year):
            if (year <= years):
                deposit = deposit + self.properties[i].deposit
        return deposit
    
    def get_net_position_at_year(self, years):
        """Net position in the portfolio"""
        # What is the net position for each property
        property_net_position = [prop.net_position_at_year(years-self.buy_year[i]) if self.buy_year[i] < years else 0 for i, prop in enumerate(self.properties)]
        return sum(property_net_position)
    
    def get_property_val(self, years):
        """Total property value"""
        property_vals = [prop.get_property_val(years-self.buy_year[i]) if self.buy_year[i] < years else 0 for i, prop in enumerate(self.properties)]
        return sum(property_vals)

    def get_usable_equity(self, years):
        """Equity which can be used to take loans"""
        #Usable equity is 80% property value - loan_left
        #Only consider positive equity
        usable_equity = [max(prop.total_equity_at_year(years-self.buy_year[i], factor=0.8),0) if self.buy_year[i] < years else 0 for i, prop in enumerate(self.properties)]
        return sum(usable_equity)
    
    def add_property(self):
        pass

    def get_personal_rent_expenditure(self, years):
        """How much is spent on rent?"""
        #One portfolio can only have one ppor property
        ppor = [(i,prop) for i, prop in enumerate(self.properties) if prop.strategy == 'ppor']
        if ppor:
            if(self.buy_year[ppor[0][0]] < years):
                return self.get_personal_rent_expenditure(self.buy_year[ppor[0][0]])
        if 'convert_to_rent' in [prop.strategy for prop in self.properties]:
            owner_occupied_years = [prop.owner_occupied_years for prop in self.properties if prop.strategy == 'convert_to_rent']
            buy_years = [self.buy_year[i] for i, prop in enumerate(self.properties) if prop.strategy == 'convert_to_rent']
            years_all = np.arange(1,years+1)
            for buy, occupied in zip(buy_years, owner_occupied_years):
                years_all = years_all[(years_all<=buy) & (years_all>buy+occupied)]
            print(years_all)
            return self.monthly_living_rent*12*len(years_all)
        else:
            return self.monthly_living_rent * 12 * years

    def get_cash_deposit_paid_at_year(self, year):
        """All properties are bought by using cash and savings"""

        return sum([prop.deposit*(1-self.equity_use_fraction[i]) if self.buy_year[i] <= year else 0 for i, prop in enumerate(self.properties)])

    def get_equity_deposit_paid_at_year(self, year):
        """All properties are bought by using cash and savings"""
        equity_needed = sum([prop.deposit*self.equity_use_fraction[i] if self.buy_year[i] <= year else 0 for i, prop in enumerate(self.properties)])
        usable_equity = self.get_usable_equity(year)
        if(equity_needed > usable_equity):
            print(f"Not enough equity at year {year} to buy property, usable equity: {usable_equity:.2f}, equity needed: {equity_needed:.2f}")
        return equity_needed

    def get_total_cash(self, years):
        """Total cash in the portfolio"""
        cash = self.cash + self.monthly_savings * 12 * years - self.get_cash_deposit_paid_at_year(years) - self.get_personal_rent_expenditure(years) + self.get_cash_flow(years)
        return cash
    

    def get_position_at_year(self, years):
        """Portfolio position at year"""
        # Total property value
        property_vals = self.get_property_val(years)
        # What is savings + left over money after buying property
        # Account for running costs
        cash = self.get_total_cash(years)
        # Any out of pocket expenses in holding the property including monthly payments
        equity = self.get_equity_at_year(years)
        net_position = self.get_net_position_at_year(years)
        return property_vals, cash, equity, net_position

    def get_position_time_series(self, year_end):
        """Get a time series of portfolio position"""
        property_vals = []
        cash = []
        equity = []
        net_position = []

        for i in range(0, year_end):
            out = self.get_position_at_year(i)
            property_vals.append(out[0])
            cash.append(out[1])
            equity.append(out[2])
            net_position.append(out[3])

        return property_vals, cash, equity, net_position


#
#    def pl_report(
#        self, years_hold, growth_rate, inflation, extra_payments, rent=0, index_rate=6
#    ):
#        sold_price = self.do_compounding(self.property_price, years_hold, growth_rate)
#        monthly = self.get_monthly_payments()
#        interest_paid = self.get_total_interest_paid(years_hold, extra_payments)
#        principal_paid = self.get_principal_paid(years_hold, extra_payments)
#        total_paid = principal_paid + self.deposit
#        sold_gain = sold_price - (self.principal - principal_paid)
#        owning_cost = total_paid + interest_paid + self.other_expenses
#        money_left = sold_gain - owning_cost
#        curr_val = money_left / (1 + growth_rate / 100) ** years_hold
#        current_principal, current_interest = self.get_stats_current_val(
#            years_hold, inflation, extra_payments
#        )
#        cur_sale = sold_price / (1 + inflation / 100) ** years_hold
#        current_own_cost = current_principal + current_interest + self.other_expenses
#        cur_sold_gain = sold_gain / (1 + inflation / 100) ** years_hold
#        current_profit = cur_sold_gain - current_own_cost
#        inflation_month = inflation / 1200
#        rent_current = (
#            rent
#            * 4
#            * (1 - (1 + inflation_month) ** (-years_hold * 12))
#            / inflation_month
#        )
#        spare_cash_if_no_buy = monthly + extra_payments - rent * 4
#        # if invested in an index fund what will be the value in years_hold
#        spare_val = (
#            spare_cash_if_no_buy
#            * ((1 + index_rate / 1200) ** (12 * years_hold) - 1)
#            * 1200
#            / index_rate
#        )
#        # what is the current value of this considering inflation
#        cur_val_spare = spare_val / (1 + inflation / 100) ** years_hold
#        out_str = f"""Property price: AUD {self.property_price} \n
#                     Loan after deposit and costs: AUD {self.principal} \n
#                     LVR: {self.principal/self.property_price} \n
#                     Minimum monthly repayments: AUD {monthly} \n
#                     Extra payments: AUD {extra_payments} \n
#                     Total monthly payments AUD: {monthly+extra_payments} \n
#                     Held the property for: {years_hold} years \n
#                     Property price in {years_hold} years with {growth_rate} percent compounding will be: AUD {sold_price} \n
#                     Total interest paid: AUD {interest_paid} \n
#                     Principal paid: AUD {principal_paid} \n
#                     Profit from selling after settling with bank: AUD {sold_gain} \n
#                     Total cost of owning: AUD {owning_cost} \n
#                     Profit: AUD {money_left} \n
#                     Current value of profit if {inflation}% discounting applied: AUD {curr_val} \n
#                     Current value of principal: AUD {current_principal} \n
#                     Current value of interest: AUD {current_interest} \n
#                     Current value of sold price: AUD {cur_sale} \n
#                     Profit based on current value: AUD {current_profit} \n
#                     Total money, principal + profit: AUD {current_principal+current_profit} \n
#                     If instead invested money left after rent in index fund, current val: AUD {cur_val_spare} \n
#       """
#        return out_str.split("\n")
#
#    def pl_report_rentvest(
#        self,
#        years_hold,
#        growth_rate,
#        inflation,
#        extra_cost,
#        interest_only,
#        rent_rentvest,
#        rent_personal,
#        reinvest
#    ):
#        sold_price = self.do_compounding(self.property_price, years_hold, growth_rate)
#        if interest_only == "Yes":
#            monthly = self.get_monthly_interest_payment()
#            principal_paid = 0
#            interest_paid = monthly*12*years_hold
#        else:
#            monthly = self.get_monthly_payments()
#            principal_paid = self.get_principal_paid(years_hold, extra_payments=0)
#            interest_paid = self.get_total_interest_paid(years_hold, extra_payments=0)
#
#        #This included other_expenses -> deposit is total of other_expenses
#        total_paid = principal_paid + self.deposit
#        sold_gain = sold_price - (self.principal - principal_paid)
#        #rent is weekly
#        rental_yield = rent_rentvest*52*years_hold
#        rental_yield_after_expenses = (rent_rentvest-extra_cost)*52*years_hold
#
#        money_left_after_mortgage = rental_yield_after_expenses - monthly*12*years_hold
#        if(money_left_after_mortgage<0):
#            after_tax = 0.7*money_left_after_mortgage
#        else:
#            after_tax = money_left_after_mortgage
#
#        personal_rent = rent_personal*52*years_hold
#
#        owning_cost = total_paid + interest_paid - rental_yield_after_expenses
#        money_left = sold_gain - owning_cost
#
#
#
#        # what is the current value of this considering inflation
#        out_str = f"""Property price: AUD {self.property_price} \n
#                     Loan after deposit and costs: AUD {self.principal} \n
#                     LVR: {self.principal/self.property_price} \n
#                     Minimum monthly repayments: AUD {monthly} \n
#                     Held the property for: {years_hold} years \n
#                     Property price in {years_hold} years with {growth_rate} percent compounding will be: AUD {sold_price} \n
#                     Total interest paid: AUD {interest_paid} \n
#                     Principal paid: AUD {principal_paid} \n
#                     Total rent received after expenses: AUD {rental_yield_after_expenses} \n
#                     Holding cost (deposit + interest paid - rent recevied): AUD {owning_cost} \n
#                     Personal rent paid: AUD {personal_rent} \n
#                     Money left after mortgage paid and rent received: AUD {money_left_after_mortgage} \n
#                     Profit from selling after settling with bank: AUD {sold_gain} \n
#                     Profit after accounting holding cost: AUD {money_left} \n
#                     Money left after selling and accouting for mortagage paid and personal rent: AUD {money_left-personal_rent}
#       """
#        return out_str.split("\n")
#
#
