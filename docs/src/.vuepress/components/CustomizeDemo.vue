<template>
  <v-card class="sharp mt-10">
    <v-card-title v-if="pythonLoading">Portfolio Laboratory (Loading index data, this may take a minute or two...)</v-card-title>
    <v-card-title v-else>Portfolio Laboratory</v-card-title>
    <v-alert
    color="info"
    v-if = "pythonLoading"
    class="sharp"
    text="Loading the latest index information from cloud storage... Give it a moment!">

    </v-alert>
    <v-alert
    color="info"
    v-if = "noIndex"
    class="sharp"
    text="All loaded! Click the highlighted 'base index' dropdown to get started by selecting a target index!">

    </v-alert>
    <v-progress-linear
      v-if="pythonLoading"
      color="primary"
      indeterminate
    ></v-progress-linear>
    <v-card-subtitle>
      <v-tabs v-model="activeSelector">
        <v-tab value="index"> Select Base Index </v-tab>
        <v-tab value="lists"> Personalize By Stock List </v-tab>
        <v-tab value="stocks"> Personalize by Stock </v-tab>
      </v-tabs>
    </v-card-subtitle>
    <div>
      <StockListSetter  v-if="activeSelector == 'lists'" :highlight="noIndex" />
      <IndexSetter v-else-if="activeSelector == 'index'" :highlight="noIndex"  />
      <StockSetter :portfolio="demoPortfolio" v-else-if="activeSelector == 'stocks'" />
    </div>
  </v-card>
  <v-divider />
  <v-skeleton-loader v-if="indexesLoading" type="card"></v-skeleton-loader>
  <TargetPortfolioView
    v-else-if="demoPortfolio.holdings"
    :portfolio="demoPortfolio"
    :targetSize="portfolioTarget"
  >
  </TargetPortfolioView>
</template>

<script lang="ts">
import TargetPortfolioView from "./target_portfolio/TargetPortfolioView.vue";
import StockListSetter from "./target_portfolio/StockListSetter.vue";
import IndexSetter from "./target_portfolio/IndexSetter.vue";
import StockSetter from "./target_portfolio/StockSetter.vue";
import { mapGetters, mapActions } from "vuex";

export default {
  components: {
    TargetPortfolioView,
    StockListSetter,
    IndexSetter,
    StockSetter,
  },
  data() {
    return {
      activeSelector: "index",
    };
  },
  methods: {
    ...mapActions(["getStockLists", "getIndexes", "getPython"]),
  },
  computed: {
    ...mapGetters([
      "demoPortfolio",
      "portfolioTarget",
      "indexesLoading",
      "pythonLoading",
    ]),
    noIndex() { 
      return !this.pythonLoading && this.demoPortfolio.holdings.length ==0 && this.activeSelector == 'index'
    }
  },
  mounted() {
    let pyodideScript = document.createElement("script");
    pyodideScript.setAttribute(
      "src",
      "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js",
    );
    pyodideScript.onload = () => {
      this.getPython().then(() => {
        console.log("demo loaded");
        this.getIndexes();
        this.getStockLists();
      });
    };
    document.head.appendChild(pyodideScript);
  },
};
</script>
<style>
.sharp {
  border-radius: 0;
}


</style>