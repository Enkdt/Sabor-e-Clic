import { useEffect, useState } from 'react'
import { fetchCooks, fetchRestaurants, affiliateCook, unaffiliateCook } from '../../authSession'
import { Header } from '../../Components/Header'
import { ConfirmDialog } from '../../Components/ConfirmDialog'
import './Affiliations.css'

export const Affiliations=()=>{
    const [cooks,setCooks]=useState([])
    const [restaurantes,setRestaurantes]=useState([])
    const [status,setStatus]=useState('loading') // loading | ready | error
    const [erro,setErro]=useState('')
    const [aRemover,setARemover]=useState(null) // { idUsuario, idRestaurante, nomeCoz, nomeRest }
    const [removendo,setRemovendo]=useState(false)

    useEffect(()=>{
        let active=true
        Promise.all([fetchCooks(), fetchRestaurants()])
            .then(([c,r])=>{ if(active){ setCooks(c); setRestaurantes(r); setStatus('ready') } })
            .catch(()=>{ if(active) setStatus('error') })
        return ()=>{ active=false }
    },[])

    const atualizar=(coz)=>setCooks((prev)=>prev.map((c)=>c.id_usuario===coz.id_usuario ? coz : c))

    const filiar=async (idUsuario, idRestaurante)=>{
        if(!idRestaurante) return
        setErro('')
        try{ atualizar(await affiliateCook(idUsuario, Number(idRestaurante))) }
        catch(err){ setErro(err.message) }
    }
    const confirmarRemocao=async ()=>{
        if(!aRemover) return
        setRemovendo(true)
        setErro('')
        try{
            atualizar(await unaffiliateCook(aRemover.idUsuario, aRemover.idRestaurante))
            setARemover(null)
        }
        catch(err){ setErro(err.message) }
        finally{ setRemovendo(false) }
    }

    return(
        <main id='conteudo-principal' className='affPage'>
            <Header/>
            <div className='affContent'>
                <h1>Filiação de cozinheiros</h1>
                <p className='affHint'>Associe cada cozinheiro aos restaurantes que ele poderá gerenciar.</p>
                {erro && <p role='alert' className='affError'>{erro}</p>}
                {status==='loading' && <p role='status'>Carregando…</p>}
                {status==='error' && <p role='alert'>Não foi possível carregar os dados.</p>}
                {status==='ready' && cooks.length===0 && <p className='affHint'>Nenhum cozinheiro cadastrado ainda.</p>}

                <ul className='affList'>
                    {cooks.map((c)=>(
                        <li key={c.id_usuario} className='affItem'>
                            <div className='affWho'>
                                <strong>{c.nome}</strong>
                                <span>{c.email}</span>
                            </div>
                            <div className='affRestaurants'>
                                {c.restaurantes.length===0 && <span className='affHint'>Sem restaurantes.</span>}
                                {c.restaurantes.map((r)=>(
                                    <span key={r.id} className='affChip'>
                                        {r.nome}
                                        <button type='button' aria-label={`Remover ${r.nome}`} onClick={()=>setARemover({ idUsuario:c.id_usuario, idRestaurante:r.id, nomeCoz:c.nome, nomeRest:r.nome })}>×</button>
                                    </span>
                                ))}
                            </div>
                            <select defaultValue='' onChange={(e)=>{ filiar(c.id_usuario, e.target.value); e.target.value='' }}>
                                <option value='' disabled>+ Filiar a restaurante…</option>
                                {restaurantes
                                    .filter((r)=>!c.restaurantes.some((cr)=>cr.id===r.id))
                                    .map((r)=>(<option key={r.id} value={r.id}>{r.nome}</option>))}
                            </select>
                        </li>
                    ))}
                </ul>
            </div>
            <ConfirmDialog
                open={aRemover!=null}
                title='Remover filiação'
                message={aRemover ? `Remover ${aRemover.nomeCoz} do restaurante "${aRemover.nomeRest}"? O cozinheiro deixará de gerenciá-lo.` : ''}
                confirmLabel='Remover'
                busy={removendo}
                onConfirm={confirmarRemocao}
                onCancel={()=>{ if(!removendo) setARemover(null) }}
            />
        </main>
    )
}
