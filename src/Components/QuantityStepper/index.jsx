import { MinusIcon, PlusIcon } from '@phosphor-icons/react'
import './QuantityStepper.css'
export const QuantityStepper=({quantity,onChange})=>{
    return(
        <div className='quantityStepper'>
            <button type='button' aria-label='Diminuir quantidade' disabled={quantity<=1} onClick={()=>onChange(quantity-1)}>
                <MinusIcon/>
            </button>
            <span>{quantity}</span>
            <button type='button' aria-label='Aumentar quantidade' onClick={()=>onChange(quantity+1)}>
                <PlusIcon/>
            </button>
        </div>
    )
}
