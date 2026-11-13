import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../authContext'
import { fetchKitchenOrders, confirmKitchenItem, denyKitchenItem } from '../authSession'
import { Header } from '../Components/Header'
import './Kitchen.css'

const STATUS_LABEL={ aguardando:'Aguardando confirmação', confirmado:'Confirmado — em preparo' }

export const Kitchen=()=>{
    const { user }=useAuth()
    const restaurantes=useMemo(()=>user?.restaurantes || [], [user])
    const [selecionado,setSelecionado]=useState(()=>restaurantes[0]?.id ?? null) // id do restaurante ativo
    const [itens,setItens]=useState([])
    const [status,setStatus]=useState('loading') // loading | ready | error
    const [busy,setBusy]=useState(null) // chave "pedido-prato" em ação
    const [error,setError]=useState('')
    const [negando,setNegando]=useState(null) // item sendo negado (abre campo de motivo)
    const [motivo,setMotivo]=useState('')

    const load=()=>{
        fetchKitchenOrders()
            .then((list)=>{ setItens(list); setStatus('ready') })
            .catch(()=>setStatus('error'))
    }

    useEffect(()=>{
        let active=true
        fetchKitchenOrders()
            .then((list)=>{ if(active){ setItens(list); setStatus('ready') } })
            .catch(()=>{ if(active) setStatus('error') })
        return ()=>{ active=false }
    },[])

    // Itens do restaurante selecionado (filtra no cliente; o backend já restringe
    // aos restaurantes do cozinheiro). Admin, sem restaurantes filiados, vê todos.
    const itensVisiveis=useMemo(()=>(
        selecionado==null ? itens : itens.filter((i)=>i.id_restaurante===selecionado)
    ),[itens,selecionado])

    const chave=(item)=>`${item.id_pedido}-${item.id_prato}`

    const confirmar=async (item)=>{
        if(busy) return
        setBusy(chave(item)); setError('')
        try{ await confirmKitchenItem(item.id_pedido,item.id_prato); load() }
        catch(err){ setError(err.message) }
        finally{ setBusy(null) }
    }

    const negar=async (item)=>{
        if(busy || !motivo.trim()) return
        setBusy(chave(item)); setError('')
        try{
            await denyKitchenItem(item.id_pedido,item.id_prato,motivo.trim())
            setNegando(null); setMotivo('')
            load()
        }catch(err){ setError(err.message) }
        finally{ setBusy(null) }
    }

    return(
        <main id='conteudo-principal' className='kitchenPage'>
            <Header/>
            <div className='kitchenContent'>
                <h1>Cozinha</h1>
                <p className='kitchenSubtitle'>Confirme ou recuse os itens dos seus restaurantes. Itens confirmados são preparados e entregues automaticamente.</p>

                {restaurantes.length>0 && (
                    <label className='kitchenDishesPicker'>Restaurante:
                        <select value={selecionado ?? ''} onChange={(e)=>setSelecionado(Number(e.target.value))}>
                            {restaurantes.map((r)=>(<option key={r.id} value={r.id}>{r.nome}</option>))}
                        </select>
                    </label>
                )}

                {status==='loading' && <p role='status'>Carregando itens…</p>}
                {status==='error' && <p role='alert'>Não foi possível carregar os itens.</p>}
                {status==='ready' && itensVisiveis.length===0 && <p>Nenhum item aguardando no momento.</p>}
                {error && <p role='alert' className='kitchenError'>{error}</p>}

                <div className='kitchenList'>
                    {status==='ready' && itensVisiveis.map((item)=>(
                        <article key={chave(item)} className='kitchenCard'>
                            <div className='kitchenCardImg' style={item.imagem ? { backgroundImage:`url(${item.imagem})` } : undefined}></div>
                            <div className='kitchenCardInfo'>
                                <h2>{`${item.quantidade} × ${item.nome}`}</h2>
                                <span className='kitchenCardMeta'>{`Pedido #${item.id_pedido} · ${item.restaurante} · ${item.cliente}`}</span>
                                <span className={`kitchenBadge kitchenBadge--${item.status}`}>{STATUS_LABEL[item.status] || item.status}</span>
                            </div>
                            {item.status==='aguardando' && (
                                <div className='kitchenCardActions'>
                                    {negando && chave(negando)===chave(item) ? (
                                        <div className='kitchenDenyBox'>
                                            <input
                                                autoFocus
                                                value={motivo}
                                                maxLength={200}
                                                placeholder='Motivo da recusa'
                                                onChange={(e)=>setMotivo(e.target.value)}
                                            />
                                            <div className='kitchenDenyActions'>
                                                <button type='button' className='kitchenDeny' disabled={!motivo.trim() || busy} onClick={()=>negar(item)}>Recusar item</button>
                                                <button type='button' className='kitchenCancel' onClick={()=>{ setNegando(null); setMotivo('') }}>Cancelar</button>
                                            </div>
                                        </div>
                                    ) : (
                                        <>
                                            <button type='button' className='kitchenConfirm' disabled={busy===chave(item)} onClick={()=>confirmar(item)}>
                                                {busy===chave(item) ? 'Confirmando…' : 'Confirmar'}
                                            </button>
                                            <button type='button' className='kitchenDeny' onClick={()=>{ setNegando(item); setMotivo('') }}>Negar</button>
                                        </>
                                    )}
                                </div>
                            )}
                        </article>
                    ))}
                </div>
            </div>
        </main>
    )
}
