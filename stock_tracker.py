import json
import os
import yfinance as yf
from typing import Dict, Optional
from rich.console import Console
from rich.table import Table

PORTFOLIO_FILE = "portfolio.json"

class StockAPI:
    """Handles fetching real-time stock data."""
    
    @staticmethod
    def get_live_price(ticker: str) -> Optional[float]:
        """Fetches the live price of a stock using yfinance."""
        try:
            # Suppress yfinance warnings to keep terminal clean
            import logging
            logging.getLogger('yfinance').setLevel(logging.CRITICAL)
            
            stock = yf.Ticker(ticker)
            
            # Try fast_info first for speed
            try:
                price = stock.fast_info['lastPrice']
                if price is not None:
                    return round(float(price), 2)
            except Exception:
                pass
                
            # Fallback to history which is more reliable for some ETFs/Funds
            hist = stock.history(period="1d")
            if not hist.empty:
                return round(float(hist['Close'].iloc[-1]), 2)
                
            return None
        except Exception:
            return None

class Portfolio:
    """Manages the user's stock portfolio."""
    
    def __init__(self, filename: str = PORTFOLIO_FILE):
        self.filename = filename
        self.holdings: Dict[str, int] = self._load()
        self.console = Console()

    def _load(self) -> Dict[str, int]:
        """Loads the portfolio from a JSON file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save(self) -> None:
        """Saves the current portfolio to a JSON file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.holdings, f, indent=4)
        except IOError as e:
            self.console.print(f"[red]Error saving portfolio: {e}[/red]")

    def add_stock(self, ticker: str, quantity: int) -> bool:
        """Adds a stock to the portfolio."""
        ticker = ticker.upper()
        if quantity <= 0:
            self.console.print("[red]Quantity must be greater than zero.[/red]")
            return False
            
        # Verify the stock exists by fetching its price
        price = StockAPI.get_live_price(ticker)
        if price is None:
            self.console.print(f"[red]Could not fetch data for ticker: {ticker}[/red]")
            return False
            
        if ticker in self.holdings:
            self.holdings[ticker] += quantity
        else:
            self.holdings[ticker] = quantity
            
        self.save()
        self.console.print(f"[green]Successfully added {quantity} shares of {ticker}![/green]")
        return True

    def remove_stock(self, ticker: str) -> bool:
        """Removes a stock from the portfolio completely."""
        ticker = ticker.upper()
        if ticker in self.holdings:
            del self.holdings[ticker]
            self.save()
            self.console.print(f"[green]Successfully removed {ticker} from your portfolio.[/green]")
            return True
        self.console.print(f"[red]{ticker} is not in your portfolio.[/red]")
        return False

    def display(self) -> None:
        """Displays the portfolio using a rich formatted table."""
        if not self.holdings:
            self.console.print("[yellow]Your portfolio is currently empty.[/yellow]")
            return

        table = Table(title="📈 Pro Stock Portfolio 📈")
        table.add_column("Ticker", style="cyan", justify="left")
        table.add_column("Shares", style="magenta", justify="right")
        table.add_column("Live Price", style="green", justify="right")
        table.add_column("Total Value", style="bold green", justify="right")

        total_portfolio_value = 0.0

        with self.console.status("[bold blue]Fetching live prices...[/bold blue]"):
            for ticker, qty in self.holdings.items():
                price = StockAPI.get_live_price(ticker)
                
                if price is not None:
                    value = price * qty
                    total_portfolio_value += value
                    table.add_row(
                        ticker, 
                        str(qty), 
                        f"${price:,.2f}", 
                        f"${value:,.2f}"
                    )
                else:
                    table.add_row(
                        ticker, 
                        str(qty), 
                        "[red]Error[/red]", 
                        "[red]N/A[/red]"
                    )

        self.console.print(table)
        self.console.print(f"[bold]Total Portfolio Value: [green]${total_portfolio_value:,.2f}[/green][/bold]\n")

def main() -> None:
    portfolio = Portfolio()
    console = Console()
    
    console.print("\n[bold blue]=== Welcome to the Pro Stock Tracker ===[/bold blue]")
    
    while True:
        console.print("\n[bold]Options:[/bold] [1] Add Stock | [2] Remove Stock | [3] View Portfolio | [4] Exit")
        choice = input("Select an option (1-4): ").strip()
        
        if choice == '1':
            ticker = input("Enter stock ticker (e.g., AAPL): ").upper().strip()
            if not ticker:
                continue
                
            qty_str = input("Enter quantity: ").strip()
            try:
                qty = int(qty_str)
                portfolio.add_stock(ticker, qty)
            except ValueError:
                console.print("[red]Invalid quantity. Please enter a whole number.[/red]")
                
        elif choice == '2':
            ticker = input("Enter stock ticker to remove: ").upper().strip()
            if ticker:
                portfolio.remove_stock(ticker)

        elif choice == '3':
            portfolio.display()
            
        elif choice == '4':
            console.print("[bold blue]Goodbye![/bold blue]")
            break
            
        else:
            console.print("[red]Invalid choice. Please select 1, 2, 3, or 4.[/red]")

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting...")
