import { AlertCircle } from "lucide-react";
import { useState } from "react";
import CheckpointsTimeline from "@/features/database-explorer/CheckpointsTimeline";
import ExplorerToolbar from "@/features/database-explorer/ExplorerToolbar";
import PhaseOperationsPanel from "@/features/database-explorer/PhaseOperationsPanel";
import SavedPopulationPanel from "@/features/database-explorer/SavedPopulationPanel";
import { useDatabaseExplorer } from "@/features/database-explorer/useDatabaseExplorer";
import AnalyticsPanel from "@/features/database-explorer/charts/AnalyticsPanel";

/**
 * Historical SQLite checkpoint explorer view composed of toolbar, error banner, and 3-column grid.
 */
function DatabaseExplorer() {
  const {
    databases,
    selectedDb,
    customDbPath,
    useCustomDb,
    experiments,
    selectedExp,
    checkpoints,
    selectedCheckpointId,
    checkpointDetail,
    populationTab,
    loading,
    apiError,
    currentExpSummary,
    displayedGenomes,
    setCustomDbPath,
    setSelectedExp,
    setSelectedCheckpointId,
    setPopulationTab,
    handleDbSelectChange,
    showDatabaseList,
    handleRefresh,
  } = useDatabaseExplorer();

  const [viewMode, setViewMode] = useState("inspector");

  return (
    <div className="explorer-wrapper">
      <ExplorerToolbar
        databases={databases}
        selectedDb={selectedDb}
        customDbPath={customDbPath}
        useCustomDb={useCustomDb}
        experiments={experiments}
        selectedExp={selectedExp}
        summary={currentExpSummary}
        loading={loading}
        viewMode={viewMode}
        onSelectDbOption={handleDbSelectChange}
        onCustomDbPathChange={setCustomDbPath}
        onShowDbList={showDatabaseList}
        onSelectExp={setSelectedExp}
        onRefresh={handleRefresh}
        onSelectViewMode={setViewMode}
      />

      {apiError && (
        <div className="explorer-error glass-panel">
          <AlertCircle size={18} />
          <span>{apiError}</span>
        </div>
      )}

      <div className="main-grid">
        <CheckpointsTimeline
          checkpoints={checkpoints}
          selectedCheckpointId={selectedCheckpointId}
          hasError={Boolean(apiError)}
          onSelectCheckpoint={setSelectedCheckpointId}
        />
        {viewMode === "inspector" ? (
          <>
            <SavedPopulationPanel
              checkpointDetail={checkpointDetail}
              populationTab={populationTab}
              displayedGenomes={displayedGenomes}
              onSelectPopulationTab={setPopulationTab}
            />
            <PhaseOperationsPanel operations={checkpointDetail?.operations} />
          </>
        ) : (
          <AnalyticsPanel
            checkpoints={checkpoints}
            checkpointDetail={checkpointDetail}
            selectedCheckpointId={selectedCheckpointId}
            onSelectCheckpoint={setSelectedCheckpointId}
          />
        )}
      </div>
    </div>
  );
}

export default DatabaseExplorer;
