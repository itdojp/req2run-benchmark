"""
Projection Implementations

Various read model projections from event stream.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

from event_store import Event
from cqrs import ReadModel


class AccountBalanceProjection(ReadModel):
    """Projects account balance from transaction events"""
    
    def __init__(self):
        super().__init__()
        self.balances: Dict[str, float] = defaultdict(float)
        self.transaction_history: Dict[str, List[Dict]] = defaultdict(list)
    
    async def project(self, event: Event):
        """Project event to update balance"""
        if event.event_type == "AccountCreated":
            account_id = event.data.get("account_id")
            initial_balance = event.data.get("initial_balance", 0)
            self.balances[account_id] = initial_balance
            
        elif event.event_type == "MoneyDeposited":
            account_id = event.data.get("account_id")
            amount = event.data.get("amount")
            self.balances[account_id] += amount
            self.transaction_history[account_id].append({
                "type": "deposit",
                "amount": amount,
                "balance": self.balances[account_id],
                "timestamp": event.timestamp.isoformat()
            })
            
        elif event.event_type == "MoneyWithdrawn":
            account_id = event.data.get("account_id")
            amount = event.data.get("amount")
            self.balances[account_id] -= amount
            self.transaction_history[account_id].append({
                "type": "withdrawal",
                "amount": amount,
                "balance": self.balances[account_id],
                "timestamp": event.timestamp.isoformat()
            })
            
        elif event.event_type == "TransferCompleted":
            from_account = event.data.get("from_account")
            to_account = event.data.get("to_account")
            amount = event.data.get("amount")
            
            self.balances[from_account] -= amount
            self.balances[to_account] += amount
            
            self.transaction_history[from_account].append({
                "type": "transfer_out",
                "amount": amount,
                "balance": self.balances[from_account],
                "to": to_account,
                "timestamp": event.timestamp.isoformat()
            })
            
            self.transaction_history[to_account].append({
                "type": "transfer_in",
                "amount": amount,
                "balance": self.balances[to_account],
                "from": from_account,
                "timestamp": event.timestamp.isoformat()
            })
    
    async def query(self, filters: Dict[str, Any]) -> Any:
        """Query account balance"""
        account_id = filters.get("account_id")
        
        if account_id:
            return {
                "account_id": account_id,
                "balance": self.balances.get(account_id, 0),
                "transaction_history": self.transaction_history.get(account_id, [])
            }
        
        # Return all balances
        return {
            "accounts": [
                {"account_id": acc_id, "balance": balance}
                for acc_id, balance in self.balances.items()
            ]
        }


class OrderSummaryProjection(ReadModel):
    """Projects order summaries from order events"""
    
    def __init__(self):
        super().__init__()
        self.orders: Dict[str, Dict] = {}
        self.customer_orders: Dict[str, List[str]] = defaultdict(list)
        self.product_orders: Dict[str, List[str]] = defaultdict(list)
        self.daily_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_orders": 0,
            "total_revenue": 0,
            "average_order_value": 0
        })
    
    async def project(self, event: Event):
        """Project event to order summary"""
        if event.event_type == "OrderCreated":
            order_id = event.aggregate_id
            customer_id = event.data.get("customer_id")
            
            self.orders[order_id] = {
                "order_id": order_id,
                "customer_id": customer_id,
                "status": "created",
                "items": [],
                "total": 0,
                "created_at": event.timestamp.isoformat(),
                "updated_at": event.timestamp.isoformat()
            }
            
            self.customer_orders[customer_id].append(order_id)
            
        elif event.event_type == "ItemAdded":
            order_id = event.aggregate_id
            if order_id in self.orders:
                item = {
                    "product_id": event.data.get("product_id"),
                    "quantity": event.data.get("quantity"),
                    "price": event.data.get("price")
                }
                self.orders[order_id]["items"].append(item)
                self.orders[order_id]["total"] += item["price"] * item["quantity"]
                self.orders[order_id]["updated_at"] = event.timestamp.isoformat()
                
                self.product_orders[item["product_id"]].append(order_id)
                
        elif event.event_type == "OrderConfirmed":
            order_id = event.aggregate_id
            if order_id in self.orders:
                self.orders[order_id]["status"] = "confirmed"
                self.orders[order_id]["updated_at"] = event.timestamp.isoformat()
                
                # Update daily stats
                date_key = event.timestamp.date().isoformat()
                self.daily_stats[date_key]["total_orders"] += 1
                self.daily_stats[date_key]["total_revenue"] += self.orders[order_id]["total"]
                self.daily_stats[date_key]["average_order_value"] = (
                    self.daily_stats[date_key]["total_revenue"] /
                    self.daily_stats[date_key]["total_orders"]
                )
                
        elif event.event_type == "OrderShipped":
            order_id = event.aggregate_id
            if order_id in self.orders:
                self.orders[order_id]["status"] = "shipped"
                self.orders[order_id]["shipped_at"] = event.timestamp.isoformat()
                self.orders[order_id]["updated_at"] = event.timestamp.isoformat()
                
        elif event.event_type == "OrderDelivered":
            order_id = event.aggregate_id
            if order_id in self.orders:
                self.orders[order_id]["status"] = "delivered"
                self.orders[order_id]["delivered_at"] = event.timestamp.isoformat()
                self.orders[order_id]["updated_at"] = event.timestamp.isoformat()
                
        elif event.event_type == "OrderCancelled":
            order_id = event.aggregate_id
            if order_id in self.orders:
                self.orders[order_id]["status"] = "cancelled"
                self.orders[order_id]["cancelled_at"] = event.timestamp.isoformat()
                self.orders[order_id]["updated_at"] = event.timestamp.isoformat()
    
    async def query(self, filters: Dict[str, Any]) -> Any:
        """Query order summaries"""
        query_type = filters.get("query_type", "order")
        
        if query_type == "order":
            order_id = filters.get("order_id")
            if order_id:
                return self.orders.get(order_id)
            
        elif query_type == "customer_orders":
            customer_id = filters.get("customer_id")
            if customer_id:
                order_ids = self.customer_orders.get(customer_id, [])
                return [self.orders[oid] for oid in order_ids if oid in self.orders]
            
        elif query_type == "product_orders":
            product_id = filters.get("product_id")
            if product_id:
                order_ids = self.product_orders.get(product_id, [])
                return [self.orders[oid] for oid in order_ids if oid in self.orders]
            
        elif query_type == "daily_stats":
            date = filters.get("date")
            if date:
                return self.daily_stats.get(date, {})
            
        elif query_type == "status":
            status = filters.get("status")
            return [
                order for order in self.orders.values()
                if order["status"] == status
            ]
        
        # Return all orders
        return list(self.orders.values())


class InventoryProjection(ReadModel):
    """Projects inventory levels from stock events"""
    
    def __init__(self):
        super().__init__()
        self.inventory: Dict[str, Dict] = {}
        self.reservations: Dict[str, List[Dict]] = defaultdict(list)
        self.movements: Dict[str, List[Dict]] = defaultdict(list)
    
    async def project(self, event: Event):
        """Project event to inventory"""
        if event.event_type == "ProductAdded":
            product_id = event.data.get("product_id")
            self.inventory[product_id] = {
                "product_id": product_id,
                "name": event.data.get("name"),
                "sku": event.data.get("sku"),
                "quantity_on_hand": 0,
                "quantity_reserved": 0,
                "quantity_available": 0,
                "reorder_point": event.data.get("reorder_point", 10),
                "reorder_quantity": event.data.get("reorder_quantity", 100)
            }
            
        elif event.event_type == "StockReceived":
            product_id = event.data.get("product_id")
            quantity = event.data.get("quantity")
            
            if product_id in self.inventory:
                self.inventory[product_id]["quantity_on_hand"] += quantity
                self.inventory[product_id]["quantity_available"] += quantity
                
                self.movements[product_id].append({
                    "type": "received",
                    "quantity": quantity,
                    "timestamp": event.timestamp.isoformat(),
                    "reference": event.data.get("reference")
                })
                
        elif event.event_type == "StockReserved":
            product_id = event.data.get("product_id")
            quantity = event.data.get("quantity")
            order_id = event.data.get("order_id")
            
            if product_id in self.inventory:
                self.inventory[product_id]["quantity_reserved"] += quantity
                self.inventory[product_id]["quantity_available"] -= quantity
                
                self.reservations[product_id].append({
                    "order_id": order_id,
                    "quantity": quantity,
                    "timestamp": event.timestamp.isoformat()
                })
                
        elif event.event_type == "StockReleased":
            product_id = event.data.get("product_id")
            quantity = event.data.get("quantity")
            order_id = event.data.get("order_id")
            
            if product_id in self.inventory:
                self.inventory[product_id]["quantity_reserved"] -= quantity
                self.inventory[product_id]["quantity_available"] += quantity
                
                # Remove reservation
                self.reservations[product_id] = [
                    r for r in self.reservations[product_id]
                    if r["order_id"] != order_id
                ]
                
        elif event.event_type == "StockShipped":
            product_id = event.data.get("product_id")
            quantity = event.data.get("quantity")
            
            if product_id in self.inventory:
                self.inventory[product_id]["quantity_on_hand"] -= quantity
                self.inventory[product_id]["quantity_reserved"] -= quantity
                
                self.movements[product_id].append({
                    "type": "shipped",
                    "quantity": quantity,
                    "timestamp": event.timestamp.isoformat(),
                    "reference": event.data.get("reference")
                })
    
    async def query(self, filters: Dict[str, Any]) -> Any:
        """Query inventory"""
        product_id = filters.get("product_id")
        
        if product_id:
            inventory = self.inventory.get(product_id, {})
            return {
                **inventory,
                "reservations": self.reservations.get(product_id, []),
                "movements": self.movements.get(product_id, [])
            }
        
        # Check for low stock
        if filters.get("low_stock"):
            return [
                inv for inv in self.inventory.values()
                if inv["quantity_available"] <= inv["reorder_point"]
            ]
        
        # Return all inventory
        return list(self.inventory.values())


class UserActivityProjection(ReadModel):
    """Projects user activity timeline from user events"""
    
    def __init__(self):
        super().__init__()
        self.users: Dict[str, Dict] = {}
        self.activities: Dict[str, List[Dict]] = defaultdict(list)
        self.sessions: Dict[str, List[Dict]] = defaultdict(list)
    
    async def project(self, event: Event):
        """Project event to user activity"""
        if event.event_type == "UserRegistered":
            user_id = event.aggregate_id
            self.users[user_id] = {
                "user_id": user_id,
                "email": event.data.get("email"),
                "name": event.data.get("name"),
                "registered_at": event.timestamp.isoformat(),
                "last_active": event.timestamp.isoformat(),
                "total_sessions": 0,
                "total_actions": 0
            }
            
            self.activities[user_id].append({
                "type": "registration",
                "timestamp": event.timestamp.isoformat(),
                "details": event.data
            })
            
        elif event.event_type == "UserLoggedIn":
            user_id = event.aggregate_id
            session_id = event.data.get("session_id")
            
            if user_id in self.users:
                self.users[user_id]["last_active"] = event.timestamp.isoformat()
                self.users[user_id]["total_sessions"] += 1
                
                self.sessions[user_id].append({
                    "session_id": session_id,
                    "started_at": event.timestamp.isoformat(),
                    "ip_address": event.data.get("ip_address"),
                    "user_agent": event.data.get("user_agent")
                })
                
                self.activities[user_id].append({
                    "type": "login",
                    "timestamp": event.timestamp.isoformat(),
                    "session_id": session_id
                })
                
        elif event.event_type == "UserAction":
            user_id = event.aggregate_id
            
            if user_id in self.users:
                self.users[user_id]["last_active"] = event.timestamp.isoformat()
                self.users[user_id]["total_actions"] += 1
                
                self.activities[user_id].append({
                    "type": "action",
                    "action": event.data.get("action"),
                    "timestamp": event.timestamp.isoformat(),
                    "details": event.data
                })
    
    async def query(self, filters: Dict[str, Any]) -> Any:
        """Query user activity"""
        user_id = filters.get("user_id")
        
        if user_id:
            user = self.users.get(user_id, {})
            return {
                **user,
                "activities": self.activities.get(user_id, []),
                "sessions": self.sessions.get(user_id, [])
            }
        
        # Get active users in time range
        if filters.get("active_since"):
            since = datetime.fromisoformat(filters["active_since"])
            return [
                user for user in self.users.values()
                if datetime.fromisoformat(user["last_active"]) >= since
            ]
        
        # Return all users
        return list(self.users.values())


class EventStreamBranching:
    """Support for event stream branching (alternative timelines)"""
    
    def __init__(self):
        self.branches: Dict[str, List[Event]] = {}
        self.branch_points: Dict[str, int] = {}
    
    async def create_branch(
        self,
        branch_name: str,
        source_stream: List[Event],
        branch_point: int
    ) -> str:
        """Create new branch from event stream"""
        # Copy events up to branch point
        self.branches[branch_name] = source_stream[:branch_point].copy()
        self.branch_points[branch_name] = branch_point
        
        return branch_name
    
    async def apply_to_branch(self, branch_name: str, events: List[Event]):
        """Apply events to branch"""
        if branch_name not in self.branches:
            raise ValueError(f"Branch {branch_name} not found")
        
        self.branches[branch_name].extend(events)
    
    async def merge_branches(
        self,
        source_branch: str,
        target_branch: str,
        conflict_resolver: callable
    ) -> List[Event]:
        """Merge two branches"""
        if source_branch not in self.branches or target_branch not in self.branches:
            raise ValueError("Branch not found")
        
        source_events = self.branches[source_branch]
        target_events = self.branches[target_branch]
        
        # Find common ancestor
        common_point = min(
            self.branch_points.get(source_branch, 0),
            self.branch_points.get(target_branch, 0)
        )
        
        # Get divergent events
        source_divergent = source_events[common_point:]
        target_divergent = target_events[common_point:]
        
        # Resolve conflicts
        merged_events = await conflict_resolver(source_divergent, target_divergent)
        
        # Update target branch
        self.branches[target_branch] = target_events[:common_point] + merged_events
        
        return self.branches[target_branch]