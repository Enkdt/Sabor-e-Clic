import { useEffect, useState } from 'react'
import { ReceiptIcon, WalletIcon } from '@phosphor-icons/react'
import { useAuth } from '../authContext'
import { fetchOrders, fetchAvatar, setAvatar, fetchBalance, addBalance } from '../authSession'
import { formatCurrency } from '../utils/formatCurrency'
import { Header } from '../Components/Header'
import { ImageUploader } from '../Components/ImageUploader'
import { OrderCard } from './OrderCard'
import './Profile.css'

export const Profile=()=>{
    const { user }=useAuth()
    const isCustomer=user?.role==='customer'
    const [orders,setOrders]=useState([])
    const [status,setStatus]=useState(isCustomer ? 'loading' : 'na') // loading | ready | error | na
    const [avatar,setAvatarUrl]=useState(null)
    const [saldo,setSaldo]=useState(null)
    const [recarga,setRecarga]=useState('50')
    const [recarregando,setRecarregando]=useState(false)

    useEffect(()=>{
        let active=true
        fetchAvatar()
            .then((url)=>{ if(active) setAvatarUrl(url) })
            .catch(()=>{}) // avatar ausente não deve quebrar o perfil
        if(!isCustomer) return ()=>{ active=false }
        fetchBalance().then((s)=>{ if(active) setSaldo(s) }).catch(()=>{})
        fetchOrders()
            .then((list)=>{ if(active){ setOrders(list); setStatus('ready') } })
            .catch(()=>{ if(active) setStatus('error') })
        return ()=>{ active=false }
    },[isCustomer])

    // Enquanto algum pedido ainda está em andamento, atualiza periodicamente para refletir
    // o avanço automático (preparando → pronto → entregue), que é derivado do tempo no servidor.
    const emAndamento=orders.some((o)=>['aguardando','preparando','pronto','confirmado'].includes(o.status))
    useEffect(()=>{
        if(!isCustomer || !emAndamento) return
        const t=setInterval(()=>{
            fetchOrders().then(setOrders).catch(()=>{})
        },15000)
        return ()=>clearInterval(t)
    },[isCustomer,emAndamento])

    const recarregar=async ()=>{
        if(recarregando) return
        setRecarregando(true)
        try{ const novo=await addBalance(Number(recarga)); setSaldo(novo) }
        catch{ /* silencioso: valor inválido é raro com os botões fixos */ }
        finally{ setRecarregando(false) }
    }

    const trocarAvatar=async (key,url)=>{
        setAvatarUrl(url)
        try{ await setAvatar(key) }catch{ /* erro já exibido pelo uploader; mantém preview */ }
    }

    return(
        <main className='profilePage'>
            <Header/>
            <section className='profileHero h-[120px] md:h-[160px]'></section>

            <div className='profileContent max-w-[1100px] mx-auto px-4'>
                <div className='profileHeader flex flex-col items-center gap-4 text-center md:flex-row md:items-end md:gap-8 md:text-left'>
                    <div className='profileAvatar' style={avatar ? { backgroundImage: `url(${avatar})` } : undefined}></div>
                    <div className='profileInfo'>
                        <h1 className='text-[32px] md:text-[40px]'>{user?.nome}</h1>
                        <p>{user?.email}</p>
                        <div className='profileAvatarEdit'>
                            <ImageUploader current={avatar} label='foto' shape='round' onUpload={trocarAvatar}/>
                        </div>
                    </div>
                </div>

                <div className='profileStats grid grid-cols-1 sm:grid-cols-3 gap-4'>
                    <div className='profileStat'>
                        <span className='profileStatIcon'><ReceiptIcon/></span>
                        <div>
                            <p className='profileStatValue'>{isCustomer && status==='ready' ? orders.length : '—'}</p>
                            <p className='profileStatLabel'>Pedidos realizados</p>
                        </div>
                    </div>
                    {isCustomer && saldo!=null && (
                        <div className='profileStat'>
                            <span className='profileStatIcon'><WalletIcon/></span>
                            <div>
                                <p className='profileStatValue'>{formatCurrency(Number(saldo))}</p>
                                <p className='profileStatLabel'>Saldo disponível</p>
                                <div className='profileRecarga'>
                                    <select value={recarga} onChange={(e)=>setRecarga(e.target.value)} aria-label='Valor da recarga'>
                                        {['20','50','100','200'].map((v)=>(<option key={v} value={v}>R$ {v}</option>))}
                                    </select>
                                    <button type='button' onClick={recarregar} disabled={recarregando}>{recarregando ? 'Adicionando…' : 'Adicionar saldo'}</button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {isCustomer ? (
                    <section className='profileOrders'>
                        <h2 className='text-[28px] md:text-[36px]'>Histórico de pedidos</h2>
                        <div className='profileOrdersList'>
                            {status==='loading' && <p role='status'>Carregando pedidos…</p>}
                            {status==='error' && <p role='alert'>Não foi possível carregar seus pedidos.</p>}
                            {status==='ready' && orders.length===0 && <p>Você ainda não fez nenhum pedido.</p>}
                            {status==='ready' && orders.map((order)=>(
                                <OrderCard key={order.id} order={order}/>
                            ))}
                        </div>
                    </section>
                ) : (
                    <section className='profileOrders'>
                        <p>{user?.role==='admin' ? 'Conta administrativa.' : 'Conta de cozinheiro.'}</p>
                    </section>
                )}
            </div>
        </main>
    )
}
