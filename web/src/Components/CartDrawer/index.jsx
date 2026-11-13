import { useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { XIcon } from '@phosphor-icons/react'
import { CartItem } from '../CartItem'
import { NextBtn } from '../NextBtn'
import { useCart } from '../../cartContext'
import { formatCurrency } from '../../utils/formatCurrency'
import './CartDrawer.css'
export const CartDrawer=({open,onClose})=>{

    const { items, subtotal, setQuantity, removeItem, clear }=useCart()

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
                            key={item.id_prato}
                            item={{ id: item.id_prato, name: item.nome, price: item.preco, quantity: item.quantity, image: item.imagem }}
                            onQuantityChange={(quantity)=>setQuantity(item.id_prato,quantity)}
                            onRemove={()=>removeItem(item.id_prato)}
                        />
                    ))}
                </div>

                <div className='cartDrawerFooter'>
                    <div className='cartDrawerTotal'>
                        <span>Total :</span>
                        <span>{formatCurrency(subtotal)}</span>
                    </div>
                    <NavLink to='/pedido' className='cartDrawerLink' onClick={onClose}>
                        <NextBtn text='Continuar'/>
                    </NavLink>
                    {items.length>0 && (
                        <button type='button' className='cartDrawerClear' onClick={clear}>Esvaziar carrinho</button>
                    )}
                    <button type='button' className='cartDrawerBack' onClick={onClose}>Voltar às compras</button>
                </div>
            </aside>
        </div>
    )
}
