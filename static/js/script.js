if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/js/service-worker.js")
        .then(() => console.log("Service Worker registrado!"))
        .catch((erro) => console.log("Erro ao registrar SW:", erro));
}


// Declaraar função que será chamada quando o usuário clicar em um pedido (recebendo o id deste pedido)
function verDetalhesPedido(id){
    // Faz uma requisição GET para o endpoint do Flask /pedido/<id> usando o valor recebido.
    fetch(`/pedidos/${id}`)
    // Transforma a resposta do servidor (que é JSON) em um objeto JavaScript.
    .then(res => res.json())
    // Começa a trabalhar com os dados recebidos da API.
    .then(data => {
        // Se a resposta tiver um erro (como "Pedido não encontrado"), mostra um alerta e encerra a função.
        if (data.erro) {
            alert(data.erro);
            return;
        }
        
        // Dados do cliente
        // Insere dinamicamente o nome, telefone e CPF do cliente dentro do elemento .info_cliente_text.
        document.querySelector(".info_cliente_text").innerHTML = `
            <p>${data.cliente.nome}</p>
            <p>${data.cliente.telefone}</p>
            <p>${data.cliente.cpf}</p>
        `;
        
        // Número do pedido
        // Mostra o número do pedido no cabeçalho da seção do pedido.
        document.querySelector(".info_num_ped").textContent = `Pedido #${data.id}`;

        // Data do pedido
        // Converte a data do pedido para formato brasileiro (ex: 18/06/2025) e atualiza o campo de data.
        const dataFormatada = new Date(data.data_pedido).toLocaleDateString("pt-BR");
        document.querySelector(".info_pedido_time").textContent = `Data: ${dataFormatada}`;

        // Tabela de itens
        // Seleciona o tbody da tabela e limpa o conteúdo anterior (caso tenha sido exibido outro pedido antes).
        const corpoTabela = document.querySelector(".info_pedido-itens tbody");
        corpoTabela.innerHTML = ""; // Limpa a tabela anterior
        //Percorre cada item do pedido e cria uma linha da tabela com os dados:
        // Nome do item
        // Cor do pano
        // Valor unitário (formatado com duas casas decimais)
        // Quantidade
        // Total
        // Cada linha é injetada dentro da tabela.
        data.itens.forEach(item => {
            const linha = `
            <tr>
                <td>${item.nome}</td>
                <td>${item.cor_pano}</td>
                <td>R$ ${item.valor_unitario.toFixed(2)}</td>
                <td>${item.quantidade}</td>
                <td>R$ ${(item.total - data.saldo).toFixed(2)}</td>
            </tr>
            `;
            corpoTabela.innerHTML += linha;
        });
        // Mostrar overlay
        // Mostra o elemento com o ID overlay, que provavelmente cobre a tela com o card de informações.
        overlay = document.getElementById("overlay");
        overlay.style.display = "block";
        document.getElementById("fechar_info_extras").addEventListener("click", () => {
            overlay.style.display = "none";
        });
    });
}

function verDetalhesCliente(id) {
    fetch(`/clientes/${id}`)
    .then(res => res.json())
    .then(data => {
        if (data.erro) {
            alert(data.erro);
            return;
        }
        const cliente_card =  document.querySelector(".info_cliente");
        cliente_card.innerHTML = "";
        cliente_card.innerHTML = `
            <button class="botoes" id="fechar_info_extras">Fechar</button>
            <button onclick="editarCliente()" class="botoes botao_editar">Editar</button>


            <picture class="info_cliente_img">
                <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" fill="currentColor" class="bi bi-person-circle" viewBox="0 0 16 16">
                    <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0"/>
                <path fill-rule="evenodd" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1"/>
                </svg>
            </picture>
            <form action="/clientes/editar" method="post" id="form_editar_cliente">
                <input type="hidden" name="id" id="edit_id" value="${data.id}">

                <label>Nome:
                    <input type="text" name="nome" id="edit_nome" value="${data.nome}" disabled>
                </label>

                <label>Número:
                    <input type="text" name="telefone" id="edit_telefone" value="${data.telefone}" disabled>
                </label>

                <label>CPF:
                    <input type="text" name="cpf" id="edit_cpf" value="${data.cpf}" disabled>
                </label>

                <button type="submit" class="botoes botao_salvar" id="btn_salvar" style="display: none;">Salvar</button>
            </form>
        `;
        overlay = document.getElementById("overlay");
        overlay.style.display = "block";
        document.getElementById("fechar_info_extras").addEventListener("click", () => {
            overlay.style.display = "none";
        });

    });   
}

function editarCliente() {
    document.getElementById("edit_nome").disabled = false;
    document.getElementById("edit_telefone").disabled = false;
    document.getElementById("edit_cpf").disabled = false;
    document.getElementById("btn_salvar").style.display = "inline-block";
}

function verDetalhesPagamento(id) {
    fetch(`/pagamentos/${id}`)
    .then(res => res.json())
    .then(data => {
        if (data.erro) {
            alert(data.erro);
            return;
        }
        const pagamentos_tabela = document.querySelector(".info_pagamento_text");
        pagamentos_tabela.innerHTML = "";
        pagamentos_tabela.innerHTML = `
            <p><strong>Pedido:</strong></p>
            <p>${data.pedido}</p>
            <p><strong>Valor Pago:</strong></p>
            <p>${data.valor_pago}</p>
            <p><strong>Data Pagamento: </strong></p>
            <p>${data.data_pagamento}</p>
        `;
        document.getElementById("overlay").style.display = "block";
    });
}

// Botão de fechar
// Quando o botão "Fechar" é clicado, oculta o card de detalhes


 