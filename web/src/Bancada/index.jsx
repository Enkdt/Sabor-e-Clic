import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../authContext'
import { Header } from '../Components/Header'
import { BancadaImg } from '../Assets/BancadaImg'
import { requestBooking } from '../authSession'
import './Bancada.css'

const brl = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)

export const Bancada = () => {
    const { id } = useParams()
    const { user } = useAuth()
    const [bancada, setBancada] = useState(null)
    const [status, setStatus] = useState('loading')
    const [inicio, setInicio] = useState('')
    const [fim, setFim] = useState('')
    const [message, setMessage] = useState('')
    const [busy, setBusy] = useState(false)

    useEffect(() => {
        let active = true
        fetch(`/api/bancadas/${encodeURIComponent(id)}`, { credentials: 'include' })
            .then(async (response) => {
                const data = await response.json()
                if (!response.ok) throw new Error(data.error?.message || 'Bancada não encontrada.')
                return data.bancada
            })
            .then((item) => { if (active) { setBancada(item); setStatus('ready') } })
            .catch(() => { if (active) setStatus('error') })
        return () => { active = false }
    }, [id])

    const estimativa = useMemo(() => {
        if (!inicio || !fim || !bancada) return null
        const minutos = (new Date(fim).getTime() - new Date(inicio).getTime()) / 60000
        if (!Number.isFinite(minutos) || minutos <= 0) return null
        return { minutos, preco: Number(bancada.preco_hora) * minutos / 60 }
    }, [inicio, fim, bancada])

    async function submit(event) {
        event.preventDefault()
        if (!bancada || !estimativa) return
        const formElement = event.currentTarget
        setBusy(true)
        setMessage('')
        try {
            const agendamento = await requestBooking(id, { inicio, fim })
            setMessage(`Pedido enviado! Aguardando a cozinha aceitar. Duração: ${agendamento.tempo_agendado} min · Total: ${brl(Number(agendamento.preco_total))} (debitado do seu saldo).`)
            setInicio('')
            setFim('')
            formElement.reset()
        } catch (error) {
            if (error.code === 'INSUFFICIENT_FUNDS') setMessage('Saldo insuficiente para solicitar esta bancada.')
            else if (error.code === 'BOOKING_CONFLICT') setMessage('Esse horário já está ocupado. Escolha outro.')
            else setMessage(error.message || 'Não foi possível conectar ao servidor.')
        } finally {
            setBusy(false)
        }
    }

    return (
        <main className='bancadaPage'>
            <Header />
            {status === 'loading' && <p role='status' className='bancadaMsg'>Carregando bancada…</p>}
            {status === 'error' && <p role='alert' className='bancadaMsg'>Não foi possível encontrar esta bancada.</p>}
            {status === 'ready' && bancada && (
                <div className='bancadaContent'>
                    <div className='bancadaHero'><BancadaImg /></div>

                    <div className='bancadaBody'>
                        <section className='bancadaInfo'>
                            <h1>{bancada.nome}</h1>
                            {bancada.endereco
                                ? <p className='bancadaAddress'>{bancada.endereco.rua}, {bancada.endereco.numero}{bancada.endereco.complemento ? ` — ${bancada.endereco.complemento}` : ''}<br />{bancada.endereco.bairro} — {bancada.endereco.cidade}, {bancada.endereco.estado}</p>
                                : <p className='bancadaAddress'>Endereço não cadastrado.</p>}
                            <p className='bancadaPrice'>Valor por hora: <strong>{brl(Number(bancada.preco_hora))}</strong></p>
                            <p>Conheça os recursos disponíveis para preparar suas receitas e impulsionar suas vendas.</p>

                            <h2 className='bancadaEquipTitle'>Equipamentos:</h2>
                            <ul className='bancadaEquip'>
                                {bancada.equipamentos.length
                                    ? bancada.equipamentos.map((item, index) => <li key={`${item.nome}-${index}`}>{item.quantidade > 1 ? `${item.quantidade} × ` : ''}{item.nome}</li>)
                                    : <li>Nenhum equipamento cadastrado.</li>}
                            </ul>
                        </section>

                        <aside className='bancadaBooking'>
                            {user?.role === 'customer' ? (
                                <>
                                    <h2>Solicitar agendamento</h2>
                                    <p className='bancadaSlots'>Horários disponíveis: {bancada.horarios_disponiveis.length
                                        ? bancada.horarios_disponiveis.map((faixa) => `${faixa.inicio}–${faixa.fim}`).join(', ')
                                        : 'sem horários cadastrados'}</p>
                                    {bancada.ocupados?.length > 0 && (
                                        <div className='bancadaOcupados'>
                                            <strong>Já ocupado:</strong>
                                            <ul>
                                                {bancada.ocupados.map((o, i) => (
                                                    <li key={i}>{new Date(o.inicio).toLocaleString('pt-BR')} – {new Date(o.fim).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    <form onSubmit={submit} className='bancadaForm'>
                                        <label>Início
                                            <input name='inicio' type='datetime-local' required value={inicio} onChange={(e) => setInicio(e.target.value)} />
                                        </label>
                                        <label>Fim
                                            <input name='fim' type='datetime-local' required value={fim} onChange={(e) => setFim(e.target.value)} />
                                        </label>
                                        {estimativa && <p className='bancadaEstimate'>Duração: {estimativa.minutos} min · Total estimado: {brl(estimativa.preco)} (debitado do saldo ao solicitar)</p>}
                                        <button type='submit' className='bancadaConfirm' disabled={busy || !estimativa}>{busy ? 'Enviando…' : 'Solicitar'}</button>
                                    </form>
                                </>
                            ) : (
                                <>
                                    <h2>Agendamento</h2>
                                    <p className='bancadaCookOnly'>
                                        {user?.role === 'cook' || user?.role === 'admin'
                                            ? 'Os pedidos de bancada dos clientes são aceitos ou recusados na área da Cozinha.'
                                            : 'Somente clientes podem solicitar o agendamento de uma bancada.'}
                                    </p>
                                    {bancada.ocupados?.length > 0 && (
                                        <div className='bancadaOcupados'>
                                            <strong>Já ocupado:</strong>
                                            <ul>
                                                {bancada.ocupados.map((o, i) => (
                                                    <li key={i}>{new Date(o.inicio).toLocaleString('pt-BR')} – {new Date(o.fim).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </>
                            )}
                            <p role='status' className='bancadaBookingMsg'>{message}</p>
                            <Link to='/catalogo/bancadas' className='bancadaBack'>Voltar ao catálogo</Link>
                        </aside>
                    </div>
                </div>
            )}
        </main>
    )
}
