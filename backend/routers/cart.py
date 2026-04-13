from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import CartItem, Product, User
from schemas import CartItemAdd, CartItemUpdate, CartItemResponse
from security import get_current_user

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _cart_to_response(item: CartItem) -> CartItemResponse:
    return CartItemResponse(
        id=item.id,
        product_id=item.product_id,
        product_name=item.product.name,
        product_price=float(item.product.price),
        quantity=item.quantity,
        added_at=item.added_at,
    )


@router.get("/", response_model=List[CartItemResponse])
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    return [_cart_to_response(i) for i in items]


@router.post("/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    data: CartItemAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < data.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    existing = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id, CartItem.product_id == data.product_id)
        .first()
    )
    if existing:
        existing.quantity += data.quantity
        db.commit()
        db.refresh(existing)
        return _cart_to_response(existing)

    item = CartItem(user_id=current_user.id, product_id=data.product_id, quantity=data.quantity)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _cart_to_response(item)


@router.put("/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    item.quantity = data.quantity
    db.commit()
    db.refresh(item)
    return _cart_to_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
