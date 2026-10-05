function onConfigTrigger(){return CardService.newCardBuilder().addSection(CardService.newCardSection().setHeader("Arkadia Attention").addWidget(CardService.newTextInput().setFieldName("arkadiaUserId").setTitle("Arkadia Firebase UID").setRequired(true))).build();}
function onManageTrigger(event){
  var c=event.workflow.triggerCreation,d=event.workflow.triggerDeletion;
  var props=PropertiesService.getUserProperties();
  if(c){props.setProperty("triggerId",c.triggerId);props.setProperty("notifyUri",c.notifyUri||("https://workspacestudio.googleapis.com/v1/triggers/"+c.triggerId+":fire"));props.setProperty("arkadiaUserId",(c.inputs.arkadiaUserId.stringValues||[""])[0]);}
  if(d){props.deleteProperty("triggerId");props.deleteProperty("notifyUri");props.deleteProperty("arkadiaUserId");}
}
