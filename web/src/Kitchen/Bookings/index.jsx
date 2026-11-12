import { useEffect, useState } from 'react'
import { fetchPendingBookings, acceptBooking, denyBooking } from '../../authSession'
import { Header } from '../../Components/Header'
import './Bookings.css'

const brl = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v)

export const KitchenBookings=()=>{
    const [itens,setItens]=useState([])
    const [status,setStatus]=useState('loading') // loading | ready | error
    const [busy,setBusy]=useState(null)
    const [error,setError]=useState('')
    const [negando,setNegando]=useState(null)
    const [motivo,setMotivo]=useState('')

    const load=()=>{
        fetchPendingBookings()
            .then((list)=>{ setItens(list); setStatus('ready') })
            .catch(()=>setStatus('error'))
    }
    useEffect(()=>{
        let active=true
        fetchPendingBookings()
            .then((list)=>{ if(active){ setItens(list); setStatus('ready') } })
            .catch(()=>{ if(active) setStatus('error') })
        return ()=>{ active=false }
    },[])

    const aceitar=async (ag)=>{
        if(busy) return
        setBusy(ag.id); setError('')
        try{ await acceptBooking(ag.id); load() }
        catch(err){ setError(err.message) }
        finally{ setBusy(null) }
    }
    const negar=async (ag)=>{
        if(busy || !motivo.trim()) return
        setBusy(ag.id); setError('')
        try{ await denyBooking(ag.id, motivo.trim()); setNegando(null); setMotivo(''); load() }
        catch(err){ setError(err.message) }
        finally{ setBusy(null) }
    }

    return(
        <main className='bookingsPage'>
            <Header/>
            <div className='bookingsContent'>
                <h1>Pedidos de bancada</h1>
                <p className='bookingsSub'>Aceite ou recuse as solicitações de agendamento dos clientes. Aceitar ocupa o horário.</p>

                {status==='loading' && <p role='status'>Carregando…</p>}
                {status==='error' && <p role='alert'>Não foi possível carregar os pedidos.</p>}
                {status==='ready' && itens.length===0 && <p>Nenhum pedido de bancada pendente.</p>}
                {error && <p role='alert' className='bookingsError'>{error}</p>}

                <ul className='bookingsList'>
                    {itens.map((ag)=>(
                        <li key={ag.id} className='bookingCard'>
                            <div className='bookingInfo'>
                                <strong>{ag.bancada}</strong>
                                <span>{new Date(ag.horario_agendado).toLocaleString('pt-BR')} · {ag.tempo_agendado} min</span>
                                <span className='bookingMeta'>{ag.cliente} · {brl(Number(ag.preco_total))}</span>
                            </div>
                            {negando?.id===ag.id ? (
                                <div className='bookingDenyBox'>
                                    <input autoFocus value={motivo} maxLength={200} placeholder='Motivo da recusa' onChange={(e)=>setMotivo(e.target.value)}/>
                                    <div className='bookingDenyActions'>
                                        <button type='button' className='bookingDeny' disabled={!motivo.trim() || busy} onClick={()=>negar(ag)}>Recusar</button>
                                        <button type='button' className='bookingCancel' onClick={()=>{ setNegando(null); setMotivo('') }}>Cancelar</button>
                                    </div>
                                </div>
                            ) : (
                                <div className='bookingActions'>
                                    <button type='button' className='bookingAccept' disabled={busy===ag.id} onClick={()=>aceitar(ag)}>{busy===ag.id ? 'Aceitando…' : 'Aceitar'}</button>
                                    <button type='button' className='bookingDeny' onClick={()=>{ setNegando(ag); setMotivo('') }}>Negar</button>
                                </div>
                            )}
                        </li>
                    ))}
                </ul>
            </div>
        </main>
    )
}
