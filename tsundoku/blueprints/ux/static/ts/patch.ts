export {};

declare global {
    interface Window {
        displayShowInfo: any;
        openAddShowModal: any;
        openEditShowModal: any;
        openDeleteShowModal: any;
        closeModals: any;
        toggleFixMatchDropdown: any;
        displayShowEntries: any;
        displayShowWebhooks: any;
        closeSearchModal: any;
        openResultUpsertModal: any;
        openAddWebhookModal: any;
        openEditWebhookModal: any;
        openDeleteWebhookModal: any;
        closeWebhookModals: any;
        closeModal: any;
        launchModal: any;
    }
}