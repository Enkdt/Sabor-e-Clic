import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { XIcon } from '@phosphor-icons/react'
import { CartItem } from '../CartItem'
import { NextBtn } from '../NextBtn'
import { cartItemsList } from '../../data/cartData'
import { formatCurrency } from '../../utils/formatCurrency'
import './CartDrawer.css'
export const CartDrawer=({open,onClose})=>{

    const [items,setItems]=useState(cartItemsList)

    useEffect(()=>{
        if(!open){
            return
        }
        const closeOnEscape=(e)=>{
            if(e.key==='Escape'){
                onClose()
            }
        }
        window.addEventListener('keydown',closeOnEscape)
        return ()=>window.removeEventListener('keydown',closeOnEscape)
    },[open,onClose])

    const total=items.reduce((sum,item)=>sum+item.price*item.quantity,0)

    const changeQuantity=(id,quantity)=>{
        setItems(items.map((item)=>item.id===id ? {...item,quantity} : item))
    }

    const removeItem=(id)=>{
        setItems(items.filter((item)=>item.id!==id))
    }

    return(
        <div className={`cartDrawerOverlay ${open ? 'open' : ''}`} onClick={onClose}>
            <aside className='cartDrawer' role='dialog' aria-label='Carrinho' onClick={(e)=>e.stopPropagation()}>
                <div className='cartDrawerHeader'>
                    <h2>{`Carrinho (${items.length})`}</h2>
                    <button type='button' aria-label='Fechar carrinho' className='cartDrawerClose' onClick={onClose}>
                        <XIcon/>
                    </button>
                </div>

                <div className='cartDrawerList'>
                    {items.length===0 && <p className='cartDrawerEmpty'>Seu carrinho está vazio</p>}
                    {items.map((item)=>(
                        <CartItem
                            key={item.id}
                            item={item}
                            onQuantityChange={(quantity)=>changeQuantity(item.id,quantity)}
                            onRemove={()=>removeItem(item.id)}
                        />
                    ))}
                </div>

                <div className='cartDrawerFooter'>
                    <div className='cartDrawerTotal'>
                        <span>Total :</span>
                        <span>{formatCurrency(total)}</span>
                    </div>
                    <NavLink to='/pedido' className='cartDrawerLink' onClick={onClose}>
                        <NextBtn text='Continuar'/>
                    </NavLink>
                    <button type='button' className='cartDrawerBack' onClick={onClose}>Voltar às compras</button>
                </div>
            </aside>
        </div>
    )
}
