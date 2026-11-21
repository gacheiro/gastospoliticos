// Filtros client-side: o site é estático, então busca e filtros
// apenas escondem/mostram elementos já presentes na página.
(function () {
    "use strict";

    // Remove acentos e caixa para comparar nomes ("João" ~ "joao").
    function normalizar(texto) {
        return (texto || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
    }

    var moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

    // --- Lista de deputados: busca por nome, UF, partido e ordenação ---
    var lista = document.getElementById("lista-deputados");
    if (lista) {
        var busca = document.getElementById("busca-nome");
        var uf = document.getElementById("filtro-uf");
        var partido = document.getElementById("filtro-partido");
        var ordem = document.getElementById("ordem");
        var contagem = document.getElementById("contagem-deputados");
        var vazio = document.getElementById("lista-vazia");
        var itens = Array.prototype.slice.call(lista.children);

        // Preenche os filtros a partir da URL (?uf=SP&partido=PT&q=nome)
        var params = new URLSearchParams(location.search);
        if (params.get("q")) busca.value = params.get("q");
        if (params.get("uf")) uf.value = params.get("uf");
        if (params.get("partido")) partido.value = params.get("partido");

        function aplicar() {
            var q = normalizar(busca.value);
            var visiveis = 0;
            itens.forEach(function (li) {
                var ok = (!q || li.dataset.nome.indexOf(q) !== -1)
                    && (!uf.value || li.dataset.uf === uf.value)
                    && (!partido.value || li.dataset.partido === partido.value);
                li.hidden = !ok;
                if (ok) visiveis++;
            });
            contagem.textContent = visiveis + (visiveis === 1 ? " deputado" : " deputados");
            vazio.hidden = visiveis !== 0;

            var novos = new URLSearchParams();
            if (busca.value) novos.set("q", busca.value);
            if (uf.value) novos.set("uf", uf.value);
            if (partido.value) novos.set("partido", partido.value);
            var qs = novos.toString();
            history.replaceState(null, "", qs ? "?" + qs : location.pathname);
        }

        function ordenar() {
            var campo = ordem.value;
            itens.sort(function (a, b) {
                if (campo === "nome") return a.dataset.nome.localeCompare(b.dataset.nome);
                return parseFloat(b.dataset[campo]) - parseFloat(a.dataset[campo]);
            });
            itens.forEach(function (li) { lista.appendChild(li); });
        }

        [busca, uf, partido].forEach(function (el) { el.addEventListener("input", aplicar); });
        ordem.addEventListener("change", ordenar);
        aplicar();
    }

    // --- Página do deputado: filtra a tabela de despesas por mês e tipo ---
    var tabela = document.getElementById("tabela-despesas");
    if (tabela) {
        var mes = document.getElementById("filtro-mes");
        var tipo = document.getElementById("filtro-tipo");
        var total = document.getElementById("total-filtrado");
        var vazioTab = document.getElementById("tabela-vazia");
        var linhas = Array.prototype.slice.call(tabela.tBodies[0].rows);

        function filtrarTabela() {
            var soma = 0, n = 0;
            linhas.forEach(function (tr) {
                var ok = (!mes.value || tr.dataset.mes === mes.value)
                    && (!tipo.value || tr.dataset.tipo === tipo.value);
                tr.hidden = !ok;
                if (ok) { soma += parseFloat(tr.dataset.valor); n++; }
            });
            total.textContent = n + (n === 1 ? " despesa" : " despesas") + " · " + moeda.format(soma);
            vazioTab.hidden = n !== 0;
        }

        mes.addEventListener("change", filtrarTabela);
        tipo.addEventListener("change", filtrarTabela);
        filtrarTabela();
    }
})();
