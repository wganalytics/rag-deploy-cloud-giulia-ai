"""Testes do portal Streamlit (portal/portal_app.py).

O script não tem guard de main(): tudo roda no import, incluindo chamadas
diretas ao Streamlit (st.set_page_config, st.columns, st.button...). Fora de
um runtime real do Streamlit essas chamadas quebrariam, então os testes
substituem o módulo `streamlit` por um MagicMock antes de importar — o que
permite rodar o script inteiro isolado e inspecionar as funções e constantes
puras que ele expõe (badge_html, PORT_MAP, load_projects, get_metrics...).
"""
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PORTAL_DIR = Path(__file__).resolve().parents[1] / "portal"
MODULE_NAME = "portal_app_under_test"


class FakeSessionState(dict):
    """Imita o st.session_state real: aceita acesso por atributo e por item."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


def _import_portal(monkeypatch, session_state=None):
    fake_st = MagicMock()
    fake_st.session_state = session_state if session_state is not None else FakeSessionState()
    # st.columns/st.tabs recebem um int ou uma lista e devolvem uma coluna/aba
    # por posição — o MagicMock padrão devolve sempre o mesmo objeto único
    # (__iter__ vazio), o que quebra o unpacking `a, b = st.columns([2, 1])`.
    fake_st.columns.side_effect = lambda spec: [MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))]
    fake_st.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    fake_st.button.return_value = False
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)

    sys.modules.pop(MODULE_NAME, None)
    spec = importlib.util.spec_from_file_location(MODULE_NAME, PORTAL_DIR / "portal_app.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module, fake_st


class TestBadgeHtml:
    def test_concluido(self, monkeypatch):
        module, _ = _import_portal(monkeypatch)
        html = module.badge_html("concluido")
        assert "Concluído" in html
        assert "badge-concluido" in html

    def test_em_desenvolvimento(self, monkeypatch):
        module, _ = _import_portal(monkeypatch)
        html = module.badge_html("em_desenvolvimento")
        assert "Em Desenvolvimento" in html
        assert "badge-em_desenvolvim" in html

    def test_status_desconhecido_cai_no_backlog(self, monkeypatch):
        module, _ = _import_portal(monkeypatch)
        html = module.badge_html("status-inexistente")
        assert "badge-backlog" in html
        assert "status-inexistente" in html


class TestPortMapAndApi:
    def test_todos_os_9_projetos_tem_porta(self, monkeypatch):
        module, _ = _import_portal(monkeypatch)
        assert set(module.PORT_MAP.keys()) == {f"PRJ-0{i}" for i in range(1, 10)}

    def test_portas_sao_unicas(self, monkeypatch):
        module, _ = _import_portal(monkeypatch)
        portas = list(module.PORT_MAP.values())
        assert len(portas) == len(set(portas))

    def test_com_api_e_subconjunto_do_port_map(self, monkeypatch):
        module, _ = _import_portal(monkeypatch)
        assert module.COM_API.issubset(set(module.PORT_MAP.keys()))


class TestRepoRoot:
    def test_encontra_a_raiz_real_do_monorepo(self, monkeypatch):
        module, _ = _import_portal(monkeypatch)
        root = module._repo_root()
        assert (root / "shared" / "REGISTRY").is_dir()
        assert (root / "dev" / "rag").is_dir()


class TestLoadProjects:
    def test_carrega_registro_real(self, monkeypatch):
        module, _ = _import_portal(monkeypatch)
        data = module.load_projects()
        assert "PRJ-01" in data.get("projetos", {})

    def test_registro_ausente_retorna_dict_vazio_e_avisa(self, monkeypatch, tmp_path):
        module, fake_st = _import_portal(monkeypatch)
        module.REPO_ROOT = tmp_path
        assert module.load_projects() == {"projetos": {}}
        fake_st.error.assert_called_once()


class TestGetMetrics:
    def test_sem_arquivo_retorna_lista_vazia(self, monkeypatch, tmp_path):
        module, _ = _import_portal(monkeypatch)
        module.REPO_ROOT = tmp_path
        assert module.get_metrics() == []

    def test_lista_json_retorna_no_maximo_os_ultimos_10(self, monkeypatch, tmp_path):
        module, _ = _import_portal(monkeypatch)
        module.REPO_ROOT = tmp_path
        log_dir = tmp_path / "observability" / "reports" / "logs"
        log_dir.mkdir(parents=True)
        registros = [{"total_latency": i} for i in range(15)]
        (log_dir / "rag_metrics.json").write_text(json.dumps(registros), encoding="utf-8")

        resultado = module.get_metrics()

        assert len(resultado) == 10
        assert resultado[-1]["total_latency"] == 14

    def test_dict_unico_vira_lista_de_um_item(self, monkeypatch, tmp_path):
        module, _ = _import_portal(monkeypatch)
        module.REPO_ROOT = tmp_path
        log_dir = tmp_path / "observability" / "reports" / "logs"
        log_dir.mkdir(parents=True)
        (log_dir / "rag_metrics.json").write_text(json.dumps({"total_latency": 1.2}), encoding="utf-8")

        assert module.get_metrics() == [{"total_latency": 1.2}]

    def test_json_com_virgula_sobrando_cai_no_fallback_linha_a_linha(self, monkeypatch, tmp_path):
        module, _ = _import_portal(monkeypatch)
        module.REPO_ROOT = tmp_path
        log_dir = tmp_path / "observability" / "reports" / "logs"
        log_dir.mkdir(parents=True)
        conteudo = '[\n{"total_latency": 1.0},\n{"total_latency": 2.0},\n]\n'
        (log_dir / "rag_metrics.json").write_text(conteudo, encoding="utf-8")

        assert module.get_metrics() == [{"total_latency": 1.0}, {"total_latency": 2.0}]


class TestLoadSnapshot:
    def test_encontra_documento_existente(self, monkeypatch, tmp_path):
        module, _ = _import_portal(monkeypatch)
        module.RAG_DIR = tmp_path
        proj_dir = tmp_path / "PRJ-01_Vanilla_RAG" / "project_context"
        proj_dir.mkdir(parents=True)
        (proj_dir / "01_OPERATIONAL_MEMORY.md").write_text("conteudo de teste", encoding="utf-8")

        assert module.load_snapshot("PRJ-01", "01_OPERATIONAL_MEMORY.md") == "conteudo de teste"

    def test_retorna_none_quando_nao_encontrado(self, monkeypatch, tmp_path):
        module, _ = _import_portal(monkeypatch)
        module.RAG_DIR = tmp_path
        assert module.load_snapshot("PRJ-99", "arquivo.md") is None


class TestScriptRodaSemExcecao:
    def test_grid_de_projetos_com_registro_real(self, monkeypatch):
        module, fake_st = _import_portal(monkeypatch)
        assert module.projects
        fake_st.set_page_config.assert_called_once()
        fake_st.title.assert_called_once()

    def test_painel_de_detalhe_com_projeto_ja_selecionado(self, monkeypatch):
        module, fake_st = _import_portal(
            monkeypatch, session_state=FakeSessionState(selected_project="PRJ-01")
        )
        # Não deve lançar exceção ao renderizar o painel de detalhe.
        assert fake_st.session_state["selected_project"] == "PRJ-01"
