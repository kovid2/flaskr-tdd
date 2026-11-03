(function () {
  console.log("ready!"); // sanity check
})();

const deleteButtons = document.getElementsByClassName("delete-btn");

for (var i = 0; i < deleteButtons.length; i++) {
  deleteButtons[i].addEventListener("click", function () {
    const postId = this.dataset.id;
    const node = this.closest(".entry");
    if (!confirm("Delete this post?")) {
      return;
    }
    fetch(`/delete/${postId}`)
      .then(function (resp) {
        return resp.json();
      })
      .then(function (result) {
        if (result.status === 1) {
          node.parentNode.removeChild(node);
          console.log(result);
        }
        location.reload();
      })
      .catch(function (err) {
        console.log(err);
      });
  });
}
