import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { cartItemsList, cartDiscount } from '../data/cartData'
import { user } from '../data/userData'
import { formatCurrency } from '../utils/formatCurrency'
import { Header } from '../Components/Header'
import { CartItem } from '../Components/CartItem'
import { NextBtn } from '../Components/NextBtn'
import './Order.css'
export const Order=()=>{

    const [items,setItems]=useState(cartItemsList)

    const subtotal=items.reduce((sum,item)=>sum+item.price*item.quantity,0)

    const changeQuantity=(id,quantity)=>{
        setItems(items.map((item)=>item.id===id ? {...item,quantity} : item))
    }

    return(
        <main className='orderPage'>
            <Header/>
            <div className='orderContent px-4 md:px-10 lg:px-[100px]'>
                <h1 className='orderTitle text-[32px] md:text-[36px]'>Meu carrinho</h1>

                <div className='orderGrid grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-8 lg:gap-[78px]'>
                    <section className='orderList'>
                        {items.map((item)=>(
                            <CartItem
                                key={item.id}
                                item={item}
                                onQuantityChange={(quantity)=>changeQuantity(item.id,quantity)}
                            />
                        ))}
                    </section>

                    <aside className='orderSummary'>
                        <h2>Endereço</h2>
                        <p className='orderAddress'>{user.address}</p>

                        <div className='orderValues'>
                            <div>
                                <span>Subtotal</span>
                                <span>{formatCurrency(subtotal)}</span>
                            </div>
                            <div>
                                <span>Descontos</span>
                                <span>{formatCurrency(cartDiscount)}</span>
                            </div>
                            <div className='orderTotal'>
                                <span>Total do Pedido</span>
                                <span>{formatCurrency(subtotal-cartDiscount)}</span>
                            </div>
                        </div>

                        <div className='orderActions'>
                            <NextBtn text='Continuar'/>
                            <NavLink to='/' className='orderAddMore'>Adicionar mais pratos</NavLink>
                        </div>
                    </aside>
                </div>
            </div>
        </main>
    )
}
