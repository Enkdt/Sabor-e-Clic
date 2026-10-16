import { AddressSelect } from '../../Components/AddressSelect'
import { Input } from '../../Components/Input'
import { NextBtn } from '../../Components/NextBtn'
import './SignUpForm.css'
export const SignUpForm=()=>{

    const inputs=[
        {
            label:"Nome",
            placeholder:"Primeiro nome",
            type:"text",
            value: ""
        },
        {
            label:"Sobrenome",
            placeholder:"Insira seu sobrenome",
            type:"text",
            value: ""
        },
        {
            label:"Email",
            placeholder:"exemplo@email.com",
            type:"text",
            value: ""
        }
    ]

    return(
        <div className='signupForm'>
            <h1 className='transition-all duration-500 ease text-[44px] md:text-[54px] lg:text-[64px]'>Bem-vindo!</h1>
            <h3 className='transition-all duration-500 ease text-[14px] lg:text-[16px]'>Cadastre-se para aproveitar todo nosso app</h3>
            <form action="">
            {inputs.map((input) => (
                                <div key={input.label}>
                                    <Input
                                        label={input.label}
                                        placeholder={input.placeholder}
                                        type={input.type}
                                        className="loginInput"
                                    />
                                </div>
                            ))}
            <label className='addressLabel'>Endereço</label>
            <AddressSelect/>
            <Input label="Rua" placeholder="Ex: Rua Augusta" type="text" className="loginInput"/>
            <div className='divNumComp'>
                <Input label="Número" placeholder="Ex: 120" type="text" className="loginInput"/>
                <Input label="Complemento" placeholder="Ex: apto 13" type="text" className="loginInput"/>
            </div>
                <Input label="Senha" placeholder="Crie sua senha" type="password" className="loginInput"/>
                <Input label="Confirmação Senha" placeholder="Repita a senha criada" type="password" className="loginInput"/>
                <NextBtn text="Criar Conta"/>
            </form>
        </div>
    )
}