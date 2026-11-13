import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useCart } from '../cartContext'
import { useAuth } from '../authContext'
import { placeOrder, payOrder, fetchAddresses } from '../authSession'
import { formatCurrency } from '../utils/formatCurrency'
import { Header } from '../Components/Header'
import { CartItem } from '../Components/CartItem'
import { NextBtn } from '../Components/NextBtn'
import './Order.css'

function formatAddress(a){
    const line1=[a.rua, a.numero].filter(Boolean).join(', ')
    const parts=[line1, a.complemento, a.bairro, [a.cidade, a.estado].filter(Boolean).join(' - '), a.cep]
    return parts.filter(Boolean).join(' · ')
}

export const Order=()=>{

    const { items, subtotal, setQuantity, clear }=useCart()
    const { user }=useAuth()
    const [status,setStatus]=useState('idle') // idle | placing | done | error
    const [message,setMessage]=useState('')
    const [pedido,setPedido]=useState(null)
    const [metodo,setMetodo]=useState('entrega')
    const [payStatus,setPayStatus]=useState('idle') // idle | paying | paid | error
    const [payMessage,setPayMessage]=useState('')
    const [address,setAddress]=useState(null)
    const [addressStatus,setAddressStatus]=useState('loading') // loading | ready | empty | error

    useEffect(()=>{
        let active=true
        fetchAddresses()
            .then((list)=>{ if(active){ setAddress(list[0] || null); setAddressStatus(list.length ? 'ready' : 'empty') } })
            .catch(()=>{ if(active) setAddressStatus('error') })
        return ()=>{ active=false }
    },[])

    const finalizar=async ()=>{
        if(status==='placing') return
        if(items.length===0){
            setStatus('error')
            setMessage('Seu carrinho está vazio.')
            return
        }
        setStatus('placing')
        setMessage('')
        try{
            const created=await placeOrder(items)
            clear()
            setPedido(created)
            setStatus('done')
        }catch(error){
            setStatus('error')
            if(error.code==='AUTHENTICATION_REQUIRED'){
                setMessage('Faça login para finalizar o pedido.')
            }else if(error.code==='EMAIL_NOT_VERIFIED'){
                setMessage('Verifique seu email antes de finalizar o pedido.')
            }else if(error.code==='PERMISSION_DENIED'){
                setMessage('Apenas clientes podem finalizar pedidos.')
            }else{
                setMessage(error.message)
            }
        }
    }

    const pagar=async ()=>{
        if(payStatus==='paying' || !pedido) return
        setPayStatus('paying')
        setPayMessage('')
        try{
            const pago=await payOrder(pedido.id,metodo)
            setPedido(pago)
            setPayStatus('paid')
        }catch(error){
            setPayStatus('error')
            setPayMessage(error.message)
        }
    }

    if(status==='done' && pedido){
        return(
            <main id='conteudo-principal' className='orderPage'>
                <Header/>
                <div className='orderContent px-4 md:px-10 lg:px-[100px]'>
                    <h1 className='orderTitle text-[32px] md:text-[36px]'>Pedido confirmado!</h1>
                    <p role='status'>Pedido #{pedido.id} criado. Total: {formatCurrency(Number(pedido.total))}.</p>
                    {pedido.pago || payStatus==='paid'
                        ? <p role='status'>Pagamento registrado ({pedido.metodo_pagamento || metodo}). Agora é só aguardar a cozinha confirmar cada item.</p>
                        : <div className='orderPayment'>
                            <h2>Pagamento</h2>
                            {user?.saldo!=null && <p className='orderSaldo'>Seu saldo: {formatCurrency(Number(user.saldo))}</p>}
                            <label>Forma de pagamento:
                                <select value={metodo} onChange={(e)=>setMetodo(e.target.value)}>
                                    <option value='entrega'>Pagar na entrega</option>
                                    <option value='pix_entrega'>PIX na entrega</option>
                                </select>
                            </label>
                            <NextBtn type='button' text={payStatus==='paying' ? 'Pagando…' : 'Pagar'} onClick={pagar}/>
                            {payStatus==='error' && <p role='alert' className='orderError'>{payMessage}</p>}
                          </div>}
                    <NavLink to='/' className='orderAddMore'>Voltar ao início</NavLink>
                </div>
            </main>
        )
    }

    return(
        <main id='conteudo-principal' className='orderPage'>
            <Header/>
            <div className='orderContent px-4 md:px-10 lg:px-[100px]'>
                <h1 className='orderTitle text-[32px] md:text-[36px]'>Meu carrinho</h1>

                <div className='orderGrid grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-8 lg:gap-[78px]'>
                    <section className='orderList'>
                        {items.length===0 && <p>Seu carrinho está vazio</p>}
                        {items.map((item)=>(
                            <CartItem
                                key={item.id_prato}
                                item={{ id: item.id_prato, name: item.nome, price: item.preco, quantity: item.quantity, image: item.imagem }}
                                onQuantityChange={(quantity)=>setQuantity(item.id_prato,quantity)}
                            />
                        ))}
                    </section>

                    <aside className='orderSummary'>
                        <h2>Endereço</h2>
                        {addressStatus==='loading' && <p className='orderAddress'>Carregando endereço…</p>}
                        {addressStatus==='ready' && address && <p className='orderAddress'>{formatAddress(address)}</p>}
                        {addressStatus==='empty' && <p className='orderAddress'>Nenhum endereço cadastrado. Entraremos em contato para confirmar a entrega.</p>}
                        {addressStatus==='error' && <p className='orderAddress' role='alert'>Não foi possível carregar seu endereço.</p>}

                        <div className='orderValues'>
                            <div>
                                <span>Subtotal</span>
                                <span>{formatCurrency(subtotal)}</span>
                            </div>
                            <div className='orderTotal'>
                                <span>Total do Pedido</span>
                                <span>{formatCurrency(subtotal)}</span>
                            </div>
                        </div>

                        <div className='orderActions'>
                            <NextBtn type='button' text={status==='placing' ? 'Finalizando…' : 'Continuar'} onClick={finalizar}/>
                            {status==='error' && <p role='alert' className='orderError'>{message}</p>}
                            <NavLink to='/' className='orderAddMore'>Adicionar mais pratos</NavLink>
                        </div>
                    </aside>
                </div>
            </div>
        </main>
    )
}
