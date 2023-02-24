from functools import lru_cache
from typing import Optional, Tuple

import numpy as np

# TODO: Add some tests
# TODO: Add functionality to borrow money from properties
# TODO: if borrowed money from offset account, take care of interest payments
# TODO: Any cash should be placed in offset account


class StrategyEnum(str):
    """Enum for strategy"""

    # principal place of residence
    ppor = "ppor"
    # Property bought for renting
    rentvest = "rentvest"
    # Property bought as ppor and converted to rentvest
    convert_to_rent = "convert_to_rent"


class Mortgage:
    """A class to do some basic calculations for Mortgage
    Extra payments can be made but they have to be constant across periods
    """

    def __init__(
        self, interest: float, loan: float, years: int, interest_only: bool = False
    ):
        # Monthly interest
        self.interest = interest / (12 * 100)
        self.loan = loan
        self.years = years
        # Compounding is being done monthly, this may not align with what banks do (daily) but close
        self.months = self.years * 12
        self.interest_only = interest_only

    def get_monthly_mortgage_payment(self) -> float:
        """Get monthly payments for the mortgage

        Returns:
            float: _Monthly payments
        """
        if self.interest_only:
            return self.get_monthly_interest_only_payment()

        return np.ceil(
            self.interest * self.loan / (1 - (1 + self.interest) ** (-self.months))
        )

    def get_monthly_interest_only_payment(self) -> float:
        """Get monthly interest only payment

        Returns:
            float: _Monthly interest only payment
        """
        return np.ceil(self.interest * self.loan)

    def get_total_interest_paid(self, years: int, extra_payments: float = 0) -> float:
        """Get total interest paid for the mortgage in years

        Args:
            years (int): _Number of years_
            extra_payments (float, optional): _Extra payments_. Defaults to 0.

        Returns:
            float: _Total interest paid_
        """
        monthly_payments = self.get_monthly_mortgage_payment() + extra_payments
        periods = years * 12
        return (self.loan * self.interest - monthly_payments) * (
            (1 + self.interest) ** periods - 1
        ) / self.interest + monthly_payments * periods

    def get_principal_remaining(self, years: int, extra_payments: float = 0) -> float:
        """Get principal remaining after years

        Args:
            years (int): Number of years
            extra_payments (float, optional): Extra payments. Defaults to 0.
        Returns:
            float: Principal remaining
        """
        interest = self.get_total_interest_paid(years, extra_payments)
        total_paid = (self.get_monthly_mortgage_payment() + extra_payments) * years * 12
        return self.loan - (total_paid - interest)

    def get_principal_paid(self, years: int, extra_payments: float = 0) -> float:
        """Get principal paid after years

        Args:
            years (int): Number of years
            extra_payments (float, optional): Extra payments. Defaults to 0.

        Returns:
            float: Principal paid
        """
        return self.loan - self.get_principal_remaining(years, extra_payments)


class Property(Mortgage):
    """A class to do some basic calculations for Property relating to property value,
    equity generated, cash flow, etc. The property can be ppor, rentvest or ppor converted to rentvest
     Year = 1 means position after owning property for one year"""

    def __init__(
        self,
        price: float,
        deposit: float,
        buying_cost: float,
        growth_rate: float,
        interest_rate: float,
        rent: float = 0,
        extra_repayments: float = 0,
        cost_growth_rate: float = 0,
        running_cost: float = 0,
        lmi: float = 0,
        strategy: StrategyEnum = "ppor",
        owner_occupied_years: Optional[float] = None,
    ):
        # Deposit is including buying cost
        # By default mortgage is for 30 years
        super().__init__(
            interest_rate,
            price - deposit + buying_cost + lmi,
            years=30,
            interest_only=True if strategy == "rentvest" else False,
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
        self.sanity_check()

    def sanity_check(self):
        """Sanity check on input parameters"""
        if self.strategy == "ppor":
            assert self.rent == 0, "PPOR should not have rent"
            assert not self.interest_only, "PPOR should not be interest only"

        if self.strategy == "rentvest":
            assert self.rent > 0, "Rentvest should have rent"

        if self.strategy == "convert_to_rent":
            assert self.rent > 0, "Convert to rent should have rent"
            assert (
                self.owner_occupied_years > 0
            ), "Convert to rent should have owner occupied years"

        assert (
            self.deposit > self.buying_cost
        ), "Deposit should be more than buying cost"
        assert self.rent >= 0, "Rent should be positive"
        assert self.strategy in [
            "ppor",
            "rentvest",
            "convert_to_rent",
        ], "Strategy should be either ppor or rentvest"
        if self.strategy == "convert_to_rent":
            assert (
                self.owner_occupied_years >= 0
            ), "Owner occupied years should be positive"

        min_repayment = self.get_monthly_mortgage_payment()
        if self.strategy == "rentvest":
            if self.rent + self.running_cost - min_repayment < 0:
                print(
                    "Running cost higher than rental income earned, property negatively geared"
                )
            else:
                print("Property positively geared")

    def get_property_position(
        self, years: int, months: float = 0
    ) -> Tuple[float, float, float]:
        """Get loan left, offset and any out of pocket expenses after holding property for years
            Out of pocker expenses include mortgage payments, running cost and any extra payments

        Args:
            years (int): Number of years property is held
            months (int, optional): [description]. Defaults to 0.

        Returns:
            Tuple(float, float, float): Loan left, offset and out of pocket expenses
        """
        if self.strategy == "convert_to_rent":
            # If property is to be converted to rent for first few years it will be normal property with 0 rent
            years_ppor = min(years, self.owner_occupied_years)
            loan_left, offset, oop = self.get_property_position_calc(
                years_ppor,
                self.get_monthly_mortgage_payment(),
                0,
                self.running_cost,
                0,
                self.loan,
                months,
            )
            # After that it will be rentvest property
            years_rentvest = max(years - years_ppor, 0)
            loan_left, offset_1, oop_1 = self.get_property_position_calc(
                years_rentvest,
                self.get_monthly_interest_only_payment(),
                self.rent,
                self.running_cost,
                offset,
                loan_left,
                months,
            )
            # offset adds on the previous offset
            return loan_left, offset_1, oop + oop_1

        else:
            return self.get_property_position_calc(
                years,
                self.get_monthly_mortgage_payment(),
                self.rent,
                self.running_cost,
                0,
                self.loan,
                months,
            )

    @lru_cache(maxsize=32)
    def get_property_position_calc(
        self,
        years: int,
        min_repayment: float,
        rent: float,
        running_cost: float,
        offset: float,
        loan: float,
        months: float = 0,
    ) -> Tuple[float, float, float]:
        """Brute force method to compute loan left, offset and out of pocket expenses after holding property for years
        Compounding is done monthly. Money can be earned from rent. Any money left after paying mortgage and running cost is put in offset account which reduces interest paid

        """

        out_of_pocket = 0

        loan_left = loan
        # min_repayment = self.get_monthly_mortgage_payment()
        periods = years * 12 + months
        for _ in range(0, periods):

            earning = rent
            # interest is not charged on any money in offset account
            interest_repayment = self.interest * (loan_left - offset)

            principal_repayments = min_repayment - interest_repayment
            # Loan left is only for interest calculation purposes, loan is not actually decreasing, money is going to offset
            loan_left = loan_left - principal_repayments
            # If earnings + extra repayments is more than min repayments then I am paying extra, otherwise coming out of pocket
            extra_repayments = (
                earning
                + self.extra_repayments
                - min_repayment
                - running_cost * (1 + self.cost_growth_rate)
            )
            out_of_pocket = out_of_pocket + min(0, extra_repayments)
            # If any extra money is left, it will go to offset account
            offset = offset + max(0, extra_repayments)

        return loan_left, offset, abs(out_of_pocket)

    def get_property_val(self, years: int) -> float:
        """Property value compounding"""
        return self.do_compounding(self.price, years, self.growth_rate)

    def get_principal_paid(self, years: int, extra_payments: float = 0) -> float:
        """How much principal has been paid in years"""
        if self.strategy == "ppor":
            return super().get_principal_paid(years, extra_payments)
        elif self.strategy in ["rentvest", "convert_to_rent"]:
            loan_left, _, _ = self.get_property_position(years)
            return self.loan - loan_left
        else:
            print(f"Strategy {self.strategy} not implemented")
            return 0

    def get_interest_paid(self, years: int) -> float:
        """How much interest has been paid in years"""
        if self.strategy in ["ppor", "rentvest"]:
            return super().get_total_interest_paid(years, self.extra_repayments)
        else:
            print(f"Strategy {self.strategy} not implemented")
            return 0

    def total_equity_at_year(self, years: int, factor: float = 1.0) -> float:
        """How much equity has been created? Equity = property value + principal paid - loan
        Equity is proerty value minus loan left"""
        property_value = self.get_property_val(years)
        principal_paid = self.get_principal_paid(years)
        equity = factor * property_value + principal_paid - self.loan
        return equity

    def get_offset_balance(self, years: int) -> float:
        """Offset balance after years"""
        _, offset, _ = self.get_property_position(years)
        return offset

    def get_oop_expenses(self, years: int) -> float:
        """Out of pocket expenses after years"""
        _, _, oop = self.get_property_position(years)
        return oop

    def get_net_cash_flow(self, years: int) -> float:
        """Net cash flow for this property if held for years, negative means cash out, positive means cash in"""
        _, offset, oop = self.get_property_position(years)
        return offset - oop

    def get_net_yearly_cash_flow(self, years: int) -> float:
        """Net cash flow for this property at year (not cumulative), negative means cash out, positive means cash in"""
        if years <= 0:
            return 0

        _, offset_1, oop_1 = self.get_property_position(years - 1)
        _, offset, oop = self.get_property_position(years)
        return (offset - oop) - (offset_1 - oop_1)

    def net_position_at_year(self, years: int) -> float:
        """Net wealth position in years
        Calculated as:
        equity - deposit - running cost - interest paid
        """
        loan_left, _, oop = self.get_property_position(years)
        net_position = self.get_property_val(years) - loan_left - self.deposit - oop

        return net_position

    def get_avg_return_at_year(self, years: int) -> float:
        """What's the profit generated from investment?
        What is the net yearly return on investment?
        """
        net_position = self.net_position_at_year(years)
        total_owning_cost = -1.0 * self.get_net_cash_flow(years) + self.deposit
        # Average yearly return?
        avg_return = (net_position / total_owning_cost * 100) / years
        return avg_return

    def get_lvr_at_year(self, years: int) -> float:
        """LVR considering payments and property growth"""
        loan_left = self.get_property_position(years)[0]
        property_val = self.get_property_val(years)
        return loan_left / property_val

    @staticmethod
    def do_compounding(principal: float, years: int, interest: float) -> float:
        """Simple compounding"""
        return principal * (1 + interest / 100) ** years


class Portfolio:
    """Class for portfolio of property which tracks performance"""

    def __init__(
        self,
        properties: list[Property],
        buy_year: list[float],
        equity_use_fraction: list[
            float
        ],  # what fraction of deposit for a property comes from equity, rest comes from cash
        cash: float,
        monthly_income: float,
        monthly_living_expenses: float,
        monthly_living_rent: float,
        income_growth_rate: float = 0,
        expenses_growth_rate: float = 0,
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

    def sanity_check(self) -> None:
        """Sanity checks for portfolio"""
        # assert self.deposits <= self.cash, "Not enough cash to buy this portfolio of properties"
        assert len(self.buy_year) == len(
            self.properties
        ), "Buy year must be specified for each property"
        assert len(self.equity_use_fraction) == len(
            self.properties
        ), "Equity use fraction must be specified for each property"
        if not self.has_ppor:
            assert (
                self.monthly_living_rent > 0
            ), "Rent cannot be 0 if no ppor proerty in portfolio"
        assert (
            len([prop for prop in self.properties if prop.strategy == "ppor"]) <= 1
        ), "Only one ppor property allowed"
        assert (
            len(
                [prop for prop in self.properties if prop.strategy == "convert_to_rent"]
            )
            <= 1
        ), "Only one convert_to_rent property allowed"

    @lru_cache(maxsize=128)
    def get_property_position(
        self, years: int, months: float = 0
    ) -> Tuple[float, float, float]:
        """Get loan left, offset and any out of pocket expenses after holding property for years
            Out of pocker expenses include mortgage payments, running cost and any extra payments

        Args:
            years (int): Number of years property is held
            months (int, optional): [description]. Defaults to 0.

        Returns:
            Tuple(float, float, float): Loan left, offset and out of pocket expenses
        """
        # How much cash do we have at t=0? It's total savings minus any deposit paid
        cash = self.cash

        n_properties = len(self.properties)

        loan_left_properties = np.zeros((years + 1, n_properties))
        oop_properties = np.zeros((years + 1, n_properties))

        total_cash = np.zeros((years + 1, 1))

        for i, property in enumerate(self.properties):
            if self.buy_year[i] > years:
                continue
            loan_left_properties[self.buy_year[i], i] = property.loan

        total_cash[0] = cash - self.get_cash_deposit_paid_at_year(0)

        for i in range(1, years + 1):

            oop_all = 0
            offset_property = 0
            # At the start of the year we buy property
            # cash = cash - self.get_cash_deposit_paid_at_year(i)
            # This is the cash left after buying
            # total_cash[i] = cash

            n_properties_active = len(
                [prop for k, prop in enumerate(self.properties) if i > self.buy_year[k]]
            )

            for j, property in enumerate(self.properties):

                if i <= self.buy_year[j]:
                    continue

                if property.strategy == "convert_to_rent":
                    if i < self.buy_year[j] + property.owner_occupied_years:
                        loan_left, offset, oop = property.get_property_position_calc(
                            1,
                            property.get_monthly_mortgage_payment(),
                            0,  # can't have rent during owner occupied periods
                            property.running_cost,
                            total_cash[i - 1, 0] * (1 / n_properties_active),
                            loan_left_properties[i - 1, j],
                            months,
                        )
                    else:
                        loan_left, offset, oop = property.get_property_position_calc(
                            1,
                            property.get_monthly_interest_only_payment(),
                            property.rent,
                            property.running_cost,
                            total_cash[i - 1, 0] * (1 / n_properties_active),
                            loan_left_properties[i - 1, j],
                            months,
                        )
                else:
                    loan_left, offset, oop = property.get_property_position_calc(
                        1,
                        property.get_monthly_mortgage_payment(),
                        property.rent,
                        property.running_cost,
                        total_cash[i - 1, 0] * (1 / n_properties_active),
                        loan_left_properties[i - 1, j],
                        months,
                    )

                # Loan left for the next year
                loan_left_properties[i, j] = loan_left
                # How much oop expenses at the end of the year
                oop_properties[i, j] = oop

                offset_property = offset_property + offset
                oop_all += oop
            # At the end of this year how much cash do we have available?
            # offset is what we earned from property, if we didn't earn anything offset will be same as input
            cash = cash + (offset_property - cash)
            cash = (
                cash
                + self.monthly_savings * 12
                - self.get_cash_deposit_paid_at_year(i)
                - self.get_personal_rent_expenditure_at_year(i)
                - oop_all
            )
            total_cash[i] = cash
        return loan_left_properties, oop_properties, total_cash

    def get_portfolio_position(self, years):
        loan_left, oop, cash = self.get_property_position(years)
        property_val = self.get_property_val(years)
        loan_left = np.sum(loan_left[:, :], axis=1)
        equity = property_val - loan_left[-1]
        return property_val, cash[-1], equity, 0

    def get_cash_flow(self, years):
        """Cash flow for the portfolio"""
        # What is the cash flow for each property

        property_cash_flow = [
            prop.get_net_cash_flow(years - self.buy_year[i])
            if self.buy_year[i] < years
            else 0
            for i, prop in enumerate(self.properties)
        ]
        return sum(property_cash_flow)

    def get_cash_flow_excluding_offset(self, years: int) -> float:
        """Cash flow for the portfolio excluding offset account"""
        # What is the cash flow for each property
        property_cash_flow = [
            prop.get_oop_expenses(years - self.buy_year[i])
            if self.buy_year[i] < years
            else 0
            for i, prop in enumerate(self.properties)
        ]
        return sum(property_cash_flow)

    def get_equity_at_year(self, years, factor=1.0):
        """Equity in the portfolio"""
        # What is the equity for each property
        property_equity = [
            prop.total_equity_at_year(years - self.buy_year[i], factor=factor)
            if self.buy_year[i] <= years
            else 0
            for i, prop in enumerate(self.properties)
        ]
        return sum(property_equity) - self.get_equity_deposit_paid_at_year(years)

    def get_deposit_needed_at_year(self, years):
        # How much deposit is needed to buy properties?
        deposit = 0
        for i, year in enumerate(self.buy_year):
            if year <= years:
                deposit = deposit + self.properties[i].deposit
        return deposit

    def get_net_position_at_year(self, years):
        """Net position in the portfolio"""
        # What is the net position for each property
        property_net_position = [
            prop.net_position_at_year(years - self.buy_year[i])
            if self.buy_year[i] < years
            else 0
            for i, prop in enumerate(self.properties)
        ]
        return sum(property_net_position)

    def get_property_val(self, years):
        """Total property value"""
        property_vals = [
            prop.get_property_val(years - self.buy_year[i])
            if self.buy_year[i] <= years
            else 0
            for i, prop in enumerate(self.properties)
        ]
        return sum(property_vals)

    def get_usable_equity(self, years):
        """Equity which can be used to take loans"""
        # Usable equity is 80% property value - loan_left
        # Only consider positive equity
        usable_equity = [
            max(prop.total_equity_at_year(years - self.buy_year[i], factor=0.8), 0)
            if self.buy_year[i] < years
            else 0
            for i, prop in enumerate(self.properties)
        ]
        return sum(usable_equity)

    def add_property(self):
        pass

    def get_personal_rent_expenditure(self, years):
        """How much is spent on rent?"""
        # One portfolio can only have one ppor property
        ppor = [
            (i, prop)
            for i, prop in enumerate(self.properties)
            if prop.strategy == "ppor"
        ]
        if ppor:
            if self.buy_year[ppor[0][0]] < years:
                return self.get_personal_rent_expenditure(self.buy_year[ppor[0][0]])
        if "convert_to_rent" in [prop.strategy for prop in self.properties]:
            owner_occupied_years = [
                prop.owner_occupied_years
                for prop in self.properties
                if prop.strategy == "convert_to_rent"
            ]
            buy_years = [
                self.buy_year[i]
                for i, prop in enumerate(self.properties)
                if prop.strategy == "convert_to_rent"
            ]
            years_all = np.arange(1, years + 1)
            for buy, occupied in zip(buy_years, owner_occupied_years):
                years_all = years_all[(years_all <= buy) & (years_all > buy + occupied)]
            return self.monthly_living_rent * 12 * len(years_all)
        else:
            return self.monthly_living_rent * 12 * years

    def get_personal_rent_expenditure_at_year(self, years):
        """How much is spent on rent?"""
        # One portfolio can only have one ppor property
        if years <= 0:
            return 0

        return self.get_personal_rent_expenditure(
            years
        ) - self.get_personal_rent_expenditure(years - 1)

    def get_total_cash_deposit_paid(self, year):
        """All properties are bought by using cash and savings"""

        return sum(
            [
                prop.deposit * (1 - self.equity_use_fraction[i])
                if self.buy_year[i] <= year
                else 0
                for i, prop in enumerate(self.properties)
            ]
        )

    def get_cash_deposit_paid_at_year(self, year):
        """All properties are bought by using cash and savings"""

        return sum(
            [
                prop.deposit * (1 - self.equity_use_fraction[i])
                if self.buy_year[i] == year
                else 0
                for i, prop in enumerate(self.properties)
            ]
        )

    def get_equity_deposit_paid_at_year(self, year):
        """All properties are bought by using cash and savings"""
        equity_needed = sum(
            [
                prop.deposit * self.equity_use_fraction[i]
                if self.buy_year[i] <= year
                else 0
                for i, prop in enumerate(self.properties)
            ]
        )
        usable_equity = self.get_usable_equity(year)
        if equity_needed > usable_equity:
            print(
                f"Not enough equity at year {year} to buy property, usable equity: {usable_equity:.2f}, equity needed: {equity_needed:.2f}"
            )
        return equity_needed

    def get_total_cash(self, years):
        """Total cash in the portfolio"""
        cash = (
            self.cash
            + self.monthly_savings * 12 * years
            - self.get_total_cash_deposit_paid(years)
            - self.get_personal_rent_expenditure(years)
            + self.get_cash_flow(years)
        )
        return cash

    def get_total_cash_excluding_offset(self, years: int) -> float:
        """Total cash in the portfolio excluding offset account"""
        cash = (
            self.cash
            + self.monthly_savings * 12 * years
            - self.get_total_cash_deposit_paid(years)
            - self.get_personal_rent_expenditure(years)
            - self.get_cash_flow_excluding_offset(years)
        )
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
            # out = self.get_position_at_year(i)
            out = self.get_portfolio_position(i)
            property_vals.append(out[0])
            cash.append(out[1])
            equity.append(out[2])
            net_position.append(out[3])

        return property_vals, cash, equity, net_position
