import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CaretDownIcon } from '@phosphor-icons/react'
import { stockCategories, stockUnits } from '../../data/stockData'
import { Header } from '../../Components/Header'
import { Input } from '../../Components/Input'
import { NextBtn } from '../../Components/NextBtn'
import './StockAdd.css'
export const StockAdd=()=>{

    const navigate=useNavigate();

    const [nome,setNome]=useState('');
    const [validade,setValidade]=useState('');
    const [quantidade,setQuantidade]=useState('');
    const [categoria,setCategoria]=useState('');
    const [unidade,setUnidade]=useState('');

    const inputs=[
        {
            label:"Nome Produto",
            placeholder:"Insira o nome do produto",
            type:"text",
            value: nome,
            onChange: (e) => setNome(e.target.value)
        },
        {
            label:"Data de validade",
            placeholder:"Insira a data de validade",
            type:"text",
            value: validade,
            onChange: (e) => setValidade(e.target.value)
        },
        {
            label:"Quantidade",
            placeholder:"Insira a quantidade do produto",
            type:"text",
            value: quantidade,
            onChange: (e) => setQuantidade(e.target.value)
        }
    ]

    const selects=[
        {
            label:"Categoria(s)",
            placeholder:"Selecione a categoria",
            options: stockCategories,
            value: categoria,
            onChange: (e) => setCategoria(e.target.value)
        },
        {
            label:"Unidade de medida",
            placeholder:"Selecione a unidade de medida",
            options: stockUnits,
            value: unidade,
            onChange: (e) => setUnidade(e.target.value)
        }
    ]

    const addItem=(e)=>{
        e.preventDefault();
        navigate('/gerente/estoque');
    }

    return(
        <main className='stockAddPage'>
            <Header/>
            <div className='stockAddForm px-4 py-8 md:px-10 lg:px-[88px]'>
                <h1 className='text-[28px] md:text-[36px]'>Adição de itens ao estoque</h1>
                <form onSubmit={addItem}>
                    {inputs.map((input)=>(
                        <Input
                            key={input.label}
                            label={input.label}
                            placeholder={input.placeholder}
                            type={input.type}
                            value={input.value}
                            onChange={input.onChange}
                            className="loginInput"
                        />
                    ))}

                    <div className='stockAddSelects grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-[40px]'>
                        {selects.map((select)=>(
                            <div key={select.label} className='stockAddField'>
                                <label>{select.label}</label>
                                <div className='stockAddSelect'>
                                    <select value={select.value} onChange={select.onChange}>
                                        <option value='' disabled>{select.placeholder}</option>
                                        {select.options.map((option)=>(
                                            <option key={option} value={option}>{option}</option>
                                        ))}
                                    </select>
                                    <CaretDownIcon className='stockAddSelectIcon'/>
                                </div>
                            </div>
                        ))}
                    </div>

                    <NextBtn text='Adicionar'/>
                </form>
            </div>
        </main>
    )
}
