import { XIcon } from '@phosphor-icons/react'
import { QuantityStepper } from '../QuantityStepper'
import { formatCurrency } from '../../utils/formatCurrency'
import './CartItem.css'
export const CartItem=({item,onQuantityChange,onRemove})=>{
    return(
        <div className='cartItem'>
            <div className='cartItemImg' style={item.image ? { backgroundImage: `url(${item.image})`, backgroundSize: 'cover', backgroundPosition: 'center' } : undefined}></div>
            <div className='cartItemInfo'>
                <p className='cartItemName'>{item.name}</p>
                <QuantityStepper quantity={item.quantity} onChange={onQuantityChange}/>
            </div>
            <p className='cartItemPrice'>{formatCurrency(item.price)}</p>
            {onRemove && (
                <button type='button' aria-label='Remover item' className='cartItemRemove' onClick={onRemove}>
                    <XIcon/>
                </button>
            )}
        </div>
    )
}
