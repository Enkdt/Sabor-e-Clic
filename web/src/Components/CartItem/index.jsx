import { XIcon } from '@phosphor-icons/react'
import { QuantityStepper } from '../QuantityStepper'
import { formatCurrency } from '../../utils/formatCurrency'
import './CartItem.css'

// Imagem padrão (stock) servida pelo backend quando o item não tem foto própria,
// garantindo que o carrinho sempre mostre uma imagem do produto.
const PLACEHOLDER_IMG = '/api/placeholder'

export const CartItem=({item,onQuantityChange,onRemove})=>{
    const imagem = item.image || PLACEHOLDER_IMG
    return(
        <div className='cartItem'>
            <div className='cartItemImg' style={{ backgroundImage: `url(${imagem})`, backgroundSize: 'cover', backgroundPosition: 'center' }}></div>
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
