import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../../authContext'
import { Header } from '../../Components/Header'
import { ImageUploader } from '../../Components/ImageUploader'
import { ConfirmDialog } from '../../Components/ConfirmDialog'
import {
    fetchRestaurant, fetchIngredients, createDish, updateDish, deleteDish, setDishImage, setDishAvailability,
} from '../../authSession'
import './Dishes.css'

const EMPTY={ nome:'', preco:'', quantidade:'', descricao:'', ingredientes:[] }

export const KitchenDishes=()=>{
    const { user }=useAuth()
    const restaurantes=useMemo(()=>user?.restaurantes || [], [user])
    const [selecionado,setSelecionado]=useState(()=>restaurantes[0]?.id ?? null) // id do restaurante ativo
    const [restaurante,setRestaurante]=useState(null) // dados carregados (com pratos)
    const [ingredientes,setIngredientes]=useState([])
    const [status,setStatus]=useState('idle') // idle | error
    const [editing,setEditing]=useState(null) // id do prato em edição ou 'novo'
    const [form,setForm]=useState(EMPTY)
    const [erro,setErro]=useState('')
    const [aExcluir,setAExcluir]=useState(null) // prato aguardando confirmação de exclusão
    const [excluindo,setExcluindo]=useState(false)

    useEffect(()=>{
        if(selecionado==null) return
        let active=true
        Promise.all([fetchRestaurant(selecionado), fetchIngredients().catch(()=>[])])
            .then(([r,ings])=>{ if(active){ setRestaurante(r); setIngredientes(ings); setStatus('idle') } })
            .catch(()=>{ if(active) setStatus('error') })
        return ()=>{ active=false }
    },[selecionado])

    const recarregar=async ()=>{
        const r=await fetchRestaurant(selecionado)
        setRestaurante(r)
    }

    const abrirNovo=()=>{ setForm(EMPTY); setEditing('novo'); setErro('') }
    const abrirEdicao=(p)=>{
        setForm({
            nome:p.nome, preco:p.preco, quantidade:String(p.quantidade), descricao:p.descricao || '',
            ingredientes:p.ingredientes.map((i)=>({ id_ingrediente:i.id_ingrediente, unidade_medida:i.unidade_medida, qtd:i.qtd })),
        })
        setEditing(p.id); setErro('')
    }

    const addIngrediente=()=>setForm((f)=>({ ...f, ingredientes:[...f.ingredientes, { id_ingrediente:ingredientes[0]?.id, unidade_medida:'un', qtd:'1' }] }))
    const setIngrediente=(idx,campo,valor)=>setForm((f)=>({ ...f, ingredientes:f.ingredientes.map((ing,i)=>i===idx ? { ...ing, [campo]:valor } : ing) }))
    const removeIngrediente=(idx)=>setForm((f)=>({ ...f, ingredientes:f.ingredientes.filter((_,i)=>i!==idx) }))

    const salvar=async (e)=>{
        e.preventDefault()
        setErro('')
        const payload={
            nome:form.nome,
            preco:form.preco,
            quantidade:Number(form.quantidade),
            descricao:form.descricao || null,
            ingredientes:form.ingredientes
                .filter((i)=>Number.isInteger(i.id_ingrediente))
                .map((i)=>({ id_ingrediente:i.id_ingrediente, unidade_medida:i.unidade_medida, qtd:String(i.qtd) })),
        }
        try{
            if(editing==='novo') await createDish(selecionado, payload)
            else await updateDish(editing, payload)
            setEditing(null)
            await recarregar()
        }catch(err){
            setErro(err.fields ? Object.values(err.fields).join(' ') : err.message)
        }
    }

    const confirmarExclusao=async ()=>{
        if(!aExcluir) return
        setExcluindo(true)
        setErro('')
        try{ await deleteDish(aExcluir.id); setAExcluir(null); await recarregar() }
        catch(err){ setErro(err.message) }
        finally{ setExcluindo(false) }
    }

    const alternarDisponibilidade=async (p)=>{
        try{ await setDishAvailability(p.id, !p.disponivel); await recarregar() }
        catch(err){ setErro(err.message) }
    }

    if(!restaurantes.length){
        return(
            <main id='conteudo-principal' className='kitchenDishesPage'>
                <Header/>
                <div className='kitchenDishesContent'>
                    <h1>Meus pratos</h1>
                    <p className='kitchenDishesEmpty'>Você ainda não está filiado a nenhum restaurante. Peça a um administrador para filiá-lo.</p>
                </div>
            </main>
        )
    }

    return(
        <main id='conteudo-principal' className='kitchenDishesPage'>
            <Header/>
            <div className='kitchenDishesContent'>
                <h1>Meus pratos</h1>

                <label className='kitchenDishesPicker'>Restaurante:
                    <select value={selecionado ?? ''} onChange={(e)=>setSelecionado(Number(e.target.value))}>
                        {restaurantes.map((r)=>(<option key={r.id} value={r.id}>{r.nome}</option>))}
                    </select>
                </label>

                {status==='error' && <p role='alert'>Não foi possível carregar o restaurante.</p>}
                {status!=='error' && !restaurante && <p role='status'>Carregando…</p>}
                {erro && <p role='alert' className='kitchenDishesError'>{erro}</p>}

                {restaurante && (
                    <>
                        <button type='button' className='kitchenDishesNew' onClick={abrirNovo}>+ Novo prato</button>
                        <ul className='kitchenDishesList'>
                            {restaurante.pratos.map((p)=>(
                                <li key={p.id} className={`kitchenDishCard${p.disponivel===false ? ' kitchenDishCard--inativo' : ''}`}>
                                    <div className='kitchenDishImg' style={p.imagem ? { backgroundImage:`url(${p.imagem})` } : undefined}></div>
                                    <div className='kitchenDishInfo'>
                                        <strong>{p.nome}{p.disponivel===false && <span className='kitchenDishUnavailable'> · indisponível</span>}</strong>
                                        <span>{`R$ ${p.preco} · ${p.quantidade} un`}</span>
                                        {p.descricao && <span className='kitchenDishDesc'>{p.descricao}</span>}
                                        <span className='kitchenDishIngs'>{p.ingredientes.map((i)=>`${i.qtd} ${i.unidade_medida} ${i.nome}`).join(', ')}</span>
                                    </div>
                                    <div className='kitchenDishActions'>
                                        <ImageUploader current={p.imagem} label='foto' onUpload={(key)=>setDishImage(p.id,key).then(recarregar).catch((e)=>setErro(e.message))}/>
                                        <button type='button' aria-pressed={p.disponivel!==false} onClick={()=>alternarDisponibilidade(p)}>{p.disponivel===false ? 'Ativar' : 'Desativar'}</button>
                                        <button type='button' onClick={()=>abrirEdicao(p)}>Editar</button>
                                        <button type='button' className='kitchenDishDelete' onClick={()=>setAExcluir(p)}>Excluir</button>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </>
                )}

                {editing && (
                    <form className='kitchenDishForm' onSubmit={salvar}>
                        <h2>{editing==='novo' ? 'Novo prato' : 'Editar prato'}</h2>
                        <label>Nome<input value={form.nome} onChange={(e)=>setForm({...form,nome:e.target.value})} required/></label>
                        <label>Preço (R$)<input type='number' step='0.01' min='0' value={form.preco} onChange={(e)=>setForm({...form,preco:e.target.value})} required/></label>
                        <label>Quantidade<input type='number' min='0' value={form.quantidade} onChange={(e)=>setForm({...form,quantidade:e.target.value})} required/></label>
                        <label>Descrição<textarea maxLength={300} value={form.descricao} onChange={(e)=>setForm({...form,descricao:e.target.value})} rows={2}/></label>

                        <div className='kitchenDishIngredients'>
                            <div className='kitchenDishIngredientsHead'>
                                <span>Ingredientes</span>
                                <button type='button' onClick={addIngrediente} disabled={!ingredientes.length}>+ Adicionar</button>
                            </div>
                            {!ingredientes.length && <p className='kitchenDishesHint'>Nenhum ingrediente no estoque ainda.</p>}
                            {form.ingredientes.map((ing,idx)=>(
                                <div key={idx} className='kitchenDishIngredientRow'>
                                    <select value={ing.id_ingrediente} onChange={(e)=>setIngrediente(idx,'id_ingrediente',Number(e.target.value))}>
                                        {ingredientes.map((i)=>(<option key={i.id} value={i.id}>{i.nome}</option>))}
                                    </select>
                                    <input type='number' step='0.01' min='0' value={ing.qtd} onChange={(e)=>setIngrediente(idx,'qtd',e.target.value)} placeholder='qtd'/>
                                    <input value={ing.unidade_medida} onChange={(e)=>setIngrediente(idx,'unidade_medida',e.target.value)} placeholder='un'/>
                                    <button type='button' onClick={()=>removeIngrediente(idx)} aria-label='Remover'>×</button>
                                </div>
                            ))}
                        </div>

                        <div className='kitchenDishFormActions'>
                            <button type='submit'>Salvar</button>
                            <button type='button' onClick={()=>setEditing(null)}>Cancelar</button>
                        </div>
                    </form>
                )}
            </div>
            <ConfirmDialog
                open={aExcluir!=null}
                title='Excluir prato'
                message={aExcluir ? `Tem certeza que deseja excluir "${aExcluir.nome}"? Esta ação não pode ser desfeita.` : ''}
                confirmLabel='Excluir'
                busy={excluindo}
                onConfirm={confirmarExclusao}
                onCancel={()=>{ if(!excluindo) setAExcluir(null) }}
            />
        </main>
    )
}
