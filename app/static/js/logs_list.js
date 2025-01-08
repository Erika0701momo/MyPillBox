const deletingModal = document.getElementById("deletingModal");
    deletingModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget; // モーダルを開いたボタン
    const date = moment(button.getAttribute("data-date")).format("L");
    const url = button.getAttribute("data-url");

    // モーダルのタイトルとボディを更新
    const modalTitle = deletingModal.querySelector(".modal-title");
    const modalBody = deletingModal.querySelector(".modal-body");
    {% if g.locale == "ja" %}
    modalTitle.textContent = `${date}の記録削除`;
    modalBody.textContent = `${date}の記録を削除します。よろしいですか？`
    {% else %}
    modalTitle.textContent = `Delete Log for ${date}`;
    modalBody.textContent = `Are you sure you want to delete the log for ${date}?`
    {% endif %}

    // フォームのactionを更新
    const form = deletingModal.querySelector("#deleteForm");
    form.action = url;
    });